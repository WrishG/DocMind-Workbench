import os
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
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    return response.text


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Uses Gemini API to generate embeddings to completely offload memory from Render Free."""
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=texts
    )
    # The API returns a list of EmbedContentResponse objects
    # Handle single string case or list of strings
    if not isinstance(response.embeddings, list):
        return [response.embeddings.values]
    
    return [e.values for e in response.embeddings]
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
        model='gemini-2.5-flash',
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
        model='gemini-2.5-flash',
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
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text
