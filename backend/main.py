from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from utils import extract_text_from_pdf, chunk_text
from vector_store import add_chunks_to_db, search_db, retrieve_and_rerank

from llm import generate_answer
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
async def upload_pdf(file : UploadFile = File(...)):
    #validate the file is a pdf
    if not file.filename.endswith(".pdf"):
        return {"error" : "Only PDF files are allowed"}

    #save file to memory 
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    raw_text = extract_text_from_pdf(file_path)
    chunks = chunk_text(raw_text, chunk_size=500, overlap=50)
    
    #add to crimadb for embeddings
    add_chunks_to_db(file.filename, chunks)
    return {
        "message": "File uploaded and processed successfully",
        "filename": file.filename,
        "total_chunks": len(chunks),
        "total_characters": len(raw_text),
        "chunks_preview": chunks[:3] if chunks else []
    }


#ask question endpint 
#this will take the question from the frontend and return the answer
#using LLM and vector store

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
