import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder

# Add this near the top where you initialized your other embedding model
# This is our Reranker. It scores how relevant a chunk is to a question.
reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')



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
def retrieve_and_rerank(query: str, top_k_initial: int = 15, top_k_final: int = 4):
    """
    1. Fetches a wide net of chunks from ChromaDB.
    2. Uses a neural network to carefully score them.
    3. Returns the absolute best chunks.
    """
    # Step 1: Get a wide net of results from ChromaDB
    initial_results = search_db(query, n_results=top_k_initial)
    
    if not initial_results:
        return []
        
    # Step 2: Prepare the pairs for the Cross-Encoder
    # The model expects a list of pairs: [[query, text1], [query, text2], ...]
    pairs = [[query, chunk["text"]] for chunk in initial_results]
    
    # Step 3: Get the strict relevance scores
    scores = reranker_model.predict(pairs)
    
    # Step 4: Attach the scores to our chunks and sort them highest to lowest
    for chunk, score in zip(initial_results, scores):
        chunk["rerank_score"] = float(score)
        
    initial_results.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    # Step 5: Return only the absolute best matches
    return initial_results[:top_k_final]

