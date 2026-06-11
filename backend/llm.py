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
