import os
import requests
from google import genai
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# The client automatically looks for GEMINI_API_KEY in the environment
client = genai.Client()

def generate_answer(question: str, retrieved_chunks: list[dict]) -> str:
    """Takes the question and the raw chunks, and asks Gemini to formulate an answer."""
    
    # 1. Combine the raw chunks into one big string for the LLM to read
    context_text = ""
    for i, chunk in enumerate(retrieved_chunks):
        context_text += f"\n--- Chunk {i+1} (Source: {chunk['source']}, Page: {chunk.get('page', 'Unknown')}) ---\n"
        context_text += chunk["text"] + "\n"

    # 2. Build the System Prompt for Gemini
    # Notice how strict we are being here. This is Prompt Engineering.
    prompt = f"""You are DocMind AI, an intelligent document analyst. 
    A user has asked a question. You must answer the question using ONLY the provided context from their documents.
    If the answer is not in the context, say "I cannot find the answer in the provided documents."
    Do not make things up.
    
    Context from documents:
    {context_text}
    
    User Question:
    {question}
    
    Please provide a clear, helpful answer:"""

    # 3. Call the API
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    
    return response.text


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Uses Gemini REST API directly to perform BATCH embeddings.
    This bypasses an SDK bug where passing a list returns a single concatenated embedding,
    and safely batches requests in groups of 100 to avoid rate limits.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:batchEmbedContents?key={api_key}"
    
    all_embeddings = []
    
    # Gemini API has a strict limit on maximum items per batch request
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        payload = {
            "requests": [
                {
                    "model": "models/gemini-embedding-2",
                    "content": {"parts": [{"text": t}]}
                }
                for t in batch_texts
            ]
        }
        
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"⚠️ Error from Gemini API: {response.text}")
            raise Exception("Failed to generate embeddings from Gemini")
            
        data = response.json()
        for emb_obj in data.get("embeddings", []):
            all_embeddings.append(emb_obj.get("values", []))
            
    return all_embeddings
# ─────────────────────────────────────────────────────────────
# TASK MODE PROMPTS
#
# Notice what changes between each function:
#   - The SAME client.models.generate_content() call
#   - The SAME Gemini model
#   - Just a different PROMPT string
#
# That's the entire secret of "Prompt Engineering".
# The LLM is a text-in, text-out machine.
# You control what it does entirely through the prompt.
# ─────────────────────────────────────────────────────────────

def classify_document(chunks: list[str]) -> str:
    """Classifies the document as Resume, Job Description, Academic Paper, or General Document."""
    context_text = "\n\n".join(chunks[:3]) # Only need the first few chunks to classify

    prompt = f"""You are an expert document classifier.
    Read the beginning of this document and classify it into exactly ONE of the following categories:
    - Resume
    - Job Description
    - Academic Paper
    - General Document

    Return ONLY the category name as a raw string. Do not explain.

    Document Content:
    {context_text}
    """

    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    classification = response.text.strip()
    valid_categories = ["Resume", "Academic Paper", "Job Description", "General Document"]
    if classification in valid_categories:
        return classification
    return "General Document"

def generate_summary(chunks: list[str]) -> str:
    """
    Takes a list of raw text chunks from a document and asks Gemini
    to produce a structured executive summary.
    No JSON needed here — just clean human-readable text.
    """
    # Join all chunks into one big string separated by newlines
    context_text = "\n\n".join(chunks)

    prompt = f"""You are an expert document analyst for DocMind Workbench.
    
    Read the following document content and produce:
    1. A 3-sentence executive summary.
    2. A bulleted list of the 5 most important key topics.
    3. One "Key Takeaway" sentence the user should remember.
    
    Document Content:
    {context_text}
    """

    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text


def generate_quiz(chunks: list[str]) -> str:
    """
    Takes document chunks and asks Gemini to produce a structured MCQ quiz.
    
    IMPORTANT: We tell Gemini to output RAW JSON only.
    This is critical for the frontend — it can parse JSON and render
    interactive buttons. It cannot parse a prose paragraph.
    This is a key Prompt Engineering technique: specifying output FORMAT.
    """
    context_text = "\n\n".join(chunks)

    prompt = f"""You are an expert professor building a quiz for DocMind Workbench.

    Read the document and generate exactly 5 multiple-choice questions.
    Base the questions ONLY on the provided document content.

    Return your response as a raw JSON array ONLY.
    Do NOT include any markdown formatting, code fences, or explanation text.
    Just output the raw JSON.

    The format must be exactly:
    [
      {{
        "question": "The question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A"
      }}
    ]

    Document Content:
    {context_text}
    """

    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text


def generate_flashcards(chunks: list[str]) -> str:
    """
    Takes document chunks and asks Gemini to extract key terms and definitions
    as flashcards, returned as a JSON array.
    
    Same pattern as generate_quiz — we force a structured JSON output
    so the frontend can render flip-cards later.
    """
    context_text = "\n\n".join(chunks)

    prompt = f"""You are a study assistant for DocMind Workbench.

    Read the document and extract 8-10 important terms or concepts as flashcards.

    Return your response as a raw JSON array ONLY.
    Do NOT include any markdown, code fences, or extra text. Just raw JSON.

    The format must be exactly:
    [
      {{
        "term": "The technical term or concept",
        "definition": "A clear, concise definition based on the document"
      }}
    ]

    Document Content:
    {context_text}
    """

    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text

# ─────────────────────────────────────────────────────────────
# SPECIALIZED AI CHAINS (Phase 3)
# ─────────────────────────────────────────────────────────────

def extract_resume_skills(chunks: list[str]) -> str:
    context_text = "\n\n".join(chunks)
    prompt = f"""You are a Technical Recruiter for DocMind Workbench.
    Extract the candidate's core skills and total years of experience from this resume.
    Return a raw JSON array of strings containing their top skills, e.g. ["Python", "React"].
    Do not include markdown or explanations.
    
    Resume:
    {context_text}
    """
    response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
    return response.text.strip()

def score_resume_match(chunks: list[str]) -> str:
    context_text = "\n\n".join(chunks)
    prompt = f"""Skeptical Senior Engineering Manager.reting the studens resume for his wellbeing
    First, read this candidate's resume and determine exactly what role they are applying for based on their experience and summary.
    Then, score this candidate strictly out of 100 based on standard industry expectations for that specific role.
    Do not be generous. Penalize for missing core fundamentals, vague impact, or lack of quantifiable metrics.
    Provide a 2-sentence explanation for the score, explicitly mentioning the role you assumed they applied for.
    Return a raw JSON object exactly like this: {{"score": 65, "explanation": "..."}}
    Do not include markdown.
    
    Resume:
    {context_text}
    """
    response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
    return response.text.strip()

def extract_paper_claims(chunks: list[str]) -> str:
    context_text = "\n\n".join(chunks[:10]) # First few chunks usually contain abstract/intro/claims
    prompt = f"""You are a peer reviewer.
    Extract the 3 main claims and 1 core limitation from this academic paper.
    Return a raw JSON object: {{"claims": ["...", "...", "..."], "limitation": "..."}}
    Do not include markdown.
    
    Paper:
    {context_text}
    """
    response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
    return response.text.strip()
