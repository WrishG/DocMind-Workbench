import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize the local database folder
# This creates a SQLite-like folder structure on your hard drive to save the vectors permanently
CHROMA_DATA_PATH = "chroma_data"
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# 2. Setup the embedding model
# all-MiniLM-L6-v2 is a lightweight model perfect for a GTX 1650. 
# It turns text into an array of 384 numbers.
embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# 3. Create or get our "collection" (Think of this like a SQL Table for vectors)
collection = client.get_or_create_collection(
    name="document_chunks",
    embedding_function=embedding_model
)

def add_chunks_to_db(filename: str, chunks: list[dict]):
    """Takes chunk dictionaries, embeds the text, and saves metadata."""
    
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    
    # NEW: We extract the text strings for embedding
    documents = [chunk["text"] for chunk in chunks]
    
    # NEW: We build metadata that includes BOTH source and page
    metadatas = [{"source": filename, "page": chunk["page"]} for chunk in chunks]
    
    # Add them to the database!
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"✅ Successfully embedded and saved {len(chunks)} chunks from {filename}")

def search_db(query: str, n_results: int = 5):
    """
    Takes a user's question, converts it to a vector, 
    and finds the closest matching chunks in the database.
    """
    
    # ChromaDB will automatically embed the query string using the model we set up
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Extract just the useful parts.
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    # Bundle them into a nice readable format
    retrieved_chunks = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        retrieved_chunks.append({
            "text": doc,
            "source": meta.get("source", "Unknown"),
            "page": meta.get("page", "Unknown"),
            "distance": dist  # Lower distance means a better match!
        })
        
    return retrieved_chunks

