import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

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


bm25_index = None
all_chunks_cache = []

def rebuild_bm25():
    """Fetches all chunks from ChromaDB and builds the keyword search index."""
    global bm25_index, all_chunks_cache
    
    # Get everything from the database
    results = collection.get()
    
    if not results or not results.get("documents"):
        return
        
    documents = results["documents"]
    metadatas = results["metadatas"]
    
    # Cache them so we can retrieve the actual text/metadata later
    all_chunks_cache = [{"text": doc, "metadata": meta} for doc, meta in zip(documents, metadatas)]
    
    # BM25 requires the text to be split into individual words (tokens)
    tokenized_corpus = [doc.lower().split(" ") for doc in documents]
    bm25_index = BM25Okapi(tokenized_corpus)

# Run it once when the server starts!
rebuild_bm25()

def keyword_search(query: str, n_results: int = 15):
    """Searches using exact keyword matching (BM25)."""
    if bm25_index is None:
        return []
        
    tokenized_query = query.lower().split(" ")
    
    # BM25 returns the full cached objects, sorted by relevance
    top_results = bm25_index.get_top_n(tokenized_query, all_chunks_cache, n=n_results)
    
    # Format them exactly like search_db formats them
    formatted_results = []
    for res in top_results:
        formatted_results.append({
            "text": res["text"],
            "source": res["metadata"].get("source", "Unknown"),
            "page": res["metadata"].get("page", "Unknown")
        })
        
    return formatted_results



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
    """Hybrid Search + Reranking Pipeline"""
    
    # 1. Semantic Search
    semantic_results = search_db(query, n_results=top_k_initial)
    
    # 2. Keyword Search
    bm25_results = keyword_search(query, n_results=top_k_initial)
    
    # 3. Combine them and remove duplicates (using the text as a unique key)
    all_results = semantic_results + bm25_results
    unique_results = {chunk["text"]: chunk for chunk in all_results}.values()
    initial_results = list(unique_results)
    
    if not initial_results:
        return []
        
    # 4. Rerank them all
    pairs = [[query, chunk["text"]] for chunk in initial_results]
    scores = reranker_model.predict(pairs)
    
    for chunk, score in zip(initial_results, scores):
        chunk["rerank_score"] = float(score)
        
    initial_results.sort(key=lambda x: x["rerank_score"], reverse=True)
    return initial_results[:top_k_final]

def get_chunks_for_file(filename: str, max_chunks: int = 10) -> list[str]:
    """
    Bypasses vector search entirely.
    Instead of searching by MEANING, we filter by METADATA.
    We just ask ChromaDB: 'give me everything where source == filename'.
    This is used by Task Modes (summarize, quiz, flashcards).
    """
    results = collection.get(
        where={"source": filename}  # metadata filter
    )
    documents = results.get("documents", [])
    # Limit to max_chunks to avoid sending a 500-page book to Gemini
    return documents[:max_chunks]
