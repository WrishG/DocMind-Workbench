from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from utils import extract_text_from_pdf, chunk_text
from vector_store import add_chunks_to_db, search_db, retrieve_and_rerank, get_chunks_for_file
from llm import generate_answer, generate_summary, generate_quiz, generate_flashcards
from database import documents_collection
from models import DocumentMetadata
from fastapi import BackgroundTasks
from workflows.engine import process_trigger

import json
import shutil
import os

#initialize
app = FastAPI(title = "DocuMind API", version = "0.1.0")

#add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
#check server is alive Health check endpoint
@app.get("/")
def root():
    return{"status":"server running", "messege" : "DocuMind API v0.1.0"}

#ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR,exist_ok=True)

#upload endpoint
@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks,file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are allowed"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    pages = extract_text_from_pdf(file_path)
    chunks = chunk_text(pages, chunk_size=500, overlap=50)
    
    # 1. AI Layer: Save math to ChromaDB
    add_chunks_to_db(file.filename, chunks)

    # 2. FSD Layer: Save metadata to MongoDB
    doc_record = DocumentMetadata(
        filename=file.filename,
        total_chunks=len(chunks)
    )
    
    # Insert it into the cloud! (We use 'await' because it's a network call)
    await documents_collection.insert_one(doc_record.model_dump(by_alias=True))

    doc_dict = {"filename": file.filename, "id": doc_record.id}
    
    # Tell FastAPI: "As soon as you reply to the user, run this function silently."
    background_tasks.add_task(process_trigger, "on_upload", doc_dict)
    return {
        "message": "File uploaded. Automations running in background!",
        "document_id": doc_record.id,
        "filename": file.filename
    }

    
# Add this endpoint so React can fetch the document library
@app.get("/documents")
async def list_documents():
    """Returns a list of all documents in the database."""
    # We query MongoDB, sort by newest first, and convert to list
    cursor = db.documents.find().sort("uploaded_at", -1)
    documents = await cursor.to_list(length=100)
    
    # Clean up the MongoDB ObjectId format for JSON
    for doc in documents:
        doc["_id"] = str(doc["_id"])
        
    return documents


#ask question endpint 
#this will take the question from the frontend and return the answer
#using LLM and vector store

# ─────────────────────────────────────────────────────────────
# TASK MODE ENDPOINTS
# These endpoints don't "search" the database.
# They pull ALL chunks for a specific file and run a specialized
# AI prompt on them (summarize, quiz, flashcards).
# ─────────────────────────────────────────────────────────────

@app.post("/summarize")
def summarize_document(payload: dict):
    """
    Input:  { "filename": "your_file.pdf" }
    Output: { "filename": "...", "summary": "..." }
    """
    filename = payload.get("filename", "")
    if not filename:
        return {"error": "filename is required"}

    # 1. Fetch the first 10 chunks of this file directly from ChromaDB
    #    (no vector search needed — we just want the document's content)
    chunks = get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'. Did you upload it?"}

    # 2. Call the summarize prompt in llm.py
    summary = generate_summary(chunks)
    return {"filename": filename, "summary": summary}


@app.post("/quiz")
def create_quiz(payload: dict):
    """
    Input:  { "filename": "your_file.pdf" }
    Output: { "filename": "...", "quiz": [ {question, options, answer}, ... ] }
    
    We force Gemini to output raw JSON so the frontend can render
    it as interactive buttons later.
    """
    filename = payload.get("filename", "")
    if not filename:
        return {"error": "filename is required"}

    chunks = get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'."}

    raw_json = generate_quiz(chunks)

    # Gemini sometimes wraps JSON in ```json ``` markdown — strip it
    raw_json = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        quiz_data = json.loads(raw_json)
        return {"filename": filename, "quiz": quiz_data}
    except Exception:
        # Fallback: return the raw text if JSON parsing fails
        return {"filename": filename, "raw_text": raw_json}


@app.post("/flashcards")
def create_flashcards(payload: dict):
    """
    Input:  { "filename": "your_file.pdf" }
    Output: { "filename": "...", "flashcards": [ {term, definition}, ... ] }
    """
    filename = payload.get("filename", "")
    if not filename:
        return {"error": "filename is required"}

    chunks = get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'."}

    raw_json = generate_flashcards(chunks)
    raw_json = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        flashcard_data = json.loads(raw_json)
        return {"filename": filename, "flashcards": flashcard_data}
    except Exception:
        return {"filename": filename, "raw_text": raw_json}


# ─────────────────────────────────────────────────────────────
# Q&A ENDPOINT (uses Hybrid Search + Reranker)
# ─────────────────────────────────────────────────────────────

@app.post("/ask")
def ask_question(payload: dict):
    question = payload.get("question", "")

    if not question:
        return {"error": "Question is required"}
    
    # ---> NEW: Advanced Retrieval Pipeline! <---
    # We fetch 15 chunks, and precisely rerank them down to the top 4.
    retrieved_docs = retrieve_and_rerank(query=question, top_k_initial=15, top_k_final=4)

    final_answer = generate_answer(question=question, retrieved_chunks=retrieved_docs)
    
    return {
        "Question": question,
        "Answer": final_answer,
        "Sources": [f"{chunk['source']} (Page {chunk.get('page', 'Unknown')}) - Score: {chunk['rerank_score']:.2f}" for chunk in retrieved_docs]
    }


# ─────────────────────────────────────────────────────────────
# WORKFLOW AUTOMATION ENDPOINTS
# ─────────────────────────────────────────────────────────────

from models import WorkflowTemplate
from database import db

@app.post("/workflow/create")
async def create_workflow(template: WorkflowTemplate):
    """
    Saves a new automation rule to the database.
    Example: When a file is uploaded (trigger), if it contains "resume" (condition), 
    generate a summary (action).
    """
    # Insert the workflow into MongoDB
    await db.workflows.insert_one(template.model_dump(by_alias=True))
    
    return {
        "message": f"Workflow '{template.name}' created successfully!",
        "workflow_id": template.id
    }
