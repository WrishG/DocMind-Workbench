from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from utils import extract_text_from_pdf, chunk_text
from vector_store import add_chunks_to_db, search_db, retrieve_and_rerank, get_chunks_for_file
from llm import generate_answer, generate_summary, generate_quiz, generate_flashcards, extract_resume_skills, score_resume_match, extract_paper_claims
from database import documents_collection, db
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
    
    # 1. AI Layer: Save math to MongoDB
    await add_chunks_to_db(file.filename, chunks)

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

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Permanently deletes a document, its vector chunks, and its file."""
    # 1. Get the document first so we know the filename
    doc = await db.documents.find_one({"_id": document_id})
    if not doc:
        return {"error": "Document not found"}

    filename = doc.get("filename")

    # 2. Delete from MongoDB Collections
    await db.documents.delete_one({"_id": document_id})
    await db.workflow_logs.delete_many({"document_id": document_id})
    if filename:
        await db.chunks.delete_many({"source": filename})

    # 3. Delete the local PDF file
    if filename:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"message": "Document and all associated data deleted successfully."}


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
async def summarize_document(payload: dict):
    filename = payload.get("filename", "")
    document_id = payload.get("document_id", "")
    
    if not filename or not document_id:
        return {"error": "filename and document_id are required"}

    # --- CACHE CHECK ---
    doc = await db.documents.find_one({"_id": document_id})
    if doc and "tasks" in doc and "summarize" in doc["tasks"]:
        print("⚡ CACHE HIT! Returning summary from MongoDB!")
        return {"filename": filename, "summary": doc["tasks"]["summarize"]}

    print("🐌 CACHE MISS! Generating new summary...")
    chunks = await get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'. Did you upload it?"}

    summary = generate_summary(chunks)
    
    # --- SAVE TO CACHE ---
    await db.documents.update_one(
        {"_id": document_id},
        {"$set": {"tasks.summarize": summary}}
    )

    return {"filename": filename, "summary": summary}


@app.post("/quiz")
async def create_quiz(payload: dict):
    filename = payload.get("filename", "")
    document_id = payload.get("document_id", "")
    
    if not filename or not document_id:
        return {"error": "filename and document_id are required"}

    # --- CACHE CHECK ---
    doc = await db.documents.find_one({"_id": document_id})
    if doc and "tasks" in doc and "quiz" in doc["tasks"]:
        print("⚡ CACHE HIT! Returning quiz from MongoDB!")
        return {"filename": filename, "quiz": doc["tasks"]["quiz"]}

    print("🐌 CACHE MISS! Generating new quiz...")
    chunks = await get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'."}

    raw_json = generate_quiz(chunks)
    raw_json = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        quiz_data = json.loads(raw_json)
        # --- SAVE TO CACHE ---
        await db.documents.update_one(
            {"_id": document_id},
            {"$set": {"tasks.quiz": quiz_data}}
        )
        return {"filename": filename, "quiz": quiz_data}
    except Exception:
        return {"filename": filename, "raw_text": raw_json}


@app.post("/flashcards")
async def create_flashcards(payload: dict):
    filename = payload.get("filename", "")
    document_id = payload.get("document_id", "")
    
    if not filename or not document_id:
        return {"error": "filename and document_id are required"}

    # --- CACHE CHECK ---
    doc = await db.documents.find_one({"_id": document_id})
    if doc and "tasks" in doc and "flashcards" in doc["tasks"]:
        print("⚡ CACHE HIT! Returning flashcards from MongoDB!")
        return {"filename": filename, "flashcards": doc["tasks"]["flashcards"]}

    print("🐌 CACHE MISS! Generating new flashcards...")
    chunks = await get_chunks_for_file(filename, max_chunks=10)
    if not chunks:
        return {"error": f"No data found for '{filename}'."}

    raw_json = generate_flashcards(chunks)
    raw_json = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        flashcard_data = json.loads(raw_json)
        # --- SAVE TO CACHE ---
        await db.documents.update_one(
            {"_id": document_id},
            {"$set": {"tasks.flashcards": flashcard_data}}
        )
        return {"filename": filename, "flashcards": flashcard_data}
    except Exception:
        return {"filename": filename, "raw_text": raw_json}


# ─────────────────────────────────────────────────────────────
# Q&A ENDPOINT (uses Hybrid Search + Reranker)
# ─────────────────────────────────────────────────────────────

@app.post("/ask")
async def ask_question(payload: dict):
    question = payload.get("question", "")
    document_id = payload.get("document_id", "")

    if not question:
        return {"error": "Question is required"}
    if not document_id:
        return {"error": "document_id is required"}
    
    # 1. Advanced Retrieval Pipeline (MongoDB Vector Search)
    retrieved_docs = await retrieve_and_rerank(query=question, top_k_initial=15, top_k_final=4)

    # 2. Generate Answer
    final_answer = generate_answer(question=question, retrieved_chunks=retrieved_docs)
    sources = [{
        "source": chunk["source"],
        "page": chunk.get("page", "Unknown"),
        "score": round(chunk["rerank_score"], 2),
        "text": chunk["text"]
    } for chunk in retrieved_docs]
    
    # 3. SAVE TO CHAT HISTORY IN MONGODB
    await db.documents.update_one(
        {"_id": document_id},
        {"$push": {
            "chat_history": {
                "$each": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "type": "chat", "content": final_answer, "sources": sources}
                ]
            }
        }}
    )
    
    return {
        "Question": question,
        "Answer": final_answer,
        "Sources": sources
    }

@app.post("/task/{task_type}")
async def run_specialized_task(task_type: str, payload: dict):
    document_id = payload.get("document_id")
    if not document_id:
        return {"error": "document_id is required"}
        
    doc = await db.documents.find_one({"_id": document_id})
    if not doc:
        return {"error": "Document not found"}
        
    filename = doc.get("filename")
    chunks = await get_chunks_for_file(filename, max_chunks=20)
    chunk_texts = chunks
    
    try:
        if task_type == "extract_skills":
            result = extract_resume_skills(chunk_texts)
        elif task_type == "score_resume":
            result = score_resume_match(chunk_texts)
        elif task_type == "extract_claims":
            result = extract_paper_claims(chunk_texts)
        else:
            return {"error": "Invalid task type"}
            
        # Clean markdown backticks to prevent JSON parsing errors
        result = result.replace("```json", "").replace("```", "").strip()
            
        # Add to chat history
        await db.documents.update_one(
            {"_id": document_id},
            {"$push": {
                "chat_history": {
                    "role": "assistant", 
                    "type": task_type, 
                    "data": {task_type: json.loads(result)} if result.startswith('{') or result.startswith('[') else {"raw_text": result}
                }
            }}
        )
        return {"status": "success", "data": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/history/{document_id}")
async def get_chat_history(document_id: str):
    """Fetches past chat history for a specific document."""
    doc = await db.documents.find_one({"_id": document_id}, {"chat_history": 1})
    if doc and "chat_history" in doc:
        return doc["chat_history"]
    return []


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
