# backend/workflows/actions.py
from vector_store import get_chunks_for_file
from llm import generate_summary, generate_quiz

def execute_action(action_type: str, filename: str):
    """
    The Switchboard: Connects a database string to an actual AI function.
    """
    # 1. Go to the Vector Database and grab the text for this specific file
    chunks = get_chunks_for_file(filename, max_chunks=10)
    
    if not chunks:
        return {"error": "No text found for this file."}

    # 2. Route the request to the correct AI Prompt
    if action_type == "run_summary":
        return generate_summary(chunks)  # Calls Gemini!
        
    elif action_type == "run_quiz":
        return generate_quiz(chunks)     # Calls Gemini!
        
    else:
        return {"error": f"Unknown action type: {action_type}"}
