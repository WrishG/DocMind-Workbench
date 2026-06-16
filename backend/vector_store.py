from sentence_transformers import CrossEncoder, SentenceTransformer
from rank_bm25 import BM25Okapi
from database import db
import asyncio

# 1. Initialize our models
# We use sentence_transformers instead of chromadb's built-in wrapper
reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# ─────────────────────────────────────────────────────────────
# DATABASE INSERTION
# ─────────────────────────────────────────────────────────────
async def add_chunks_to_db(filename: str, chunks: list[dict]):
    """Takes chunk dictionaries, embeds the text, and saves to MongoDB."""
    
    # Generate embeddings for all chunks at once
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    
    # Prepare documents for MongoDB
    db_documents = []
    for i, chunk in enumerate(chunks):
        db_documents.append({
            "source": filename,
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": embeddings[i] # The vector!
        })
        
    # Insert into the db.chunks collection
    await db.chunks.insert_many(db_documents)
    print(f"✅ Successfully embedded and saved {len(chunks)} chunks from {filename} to MongoDB Atlas")
    
    # Rebuild the BM25 index since we added new data
    await rebuild_bm25()


# ─────────────────────────────────────────────────────────────
# KEYWORD SEARCH (BM25)
# ─────────────────────────────────────────────────────────────
bm25_index = None
all_chunks_cache = []

async def rebuild_bm25():
    """Fetches all chunks from MongoDB and builds the keyword search index."""
    global bm25_index, all_chunks_cache
    
    # Get all chunks from MongoDB
    cursor = db.chunks.find({}, {"text": 1, "source": 1, "page": 1})
    results = await cursor.to_list(length=10000)
    
    if not results:
        return
        
    # Cache them so we can retrieve the actual text/metadata later
    all_chunks_cache = [{"text": doc["text"], "metadata": {"source": doc["source"], "page": doc["page"]}} for doc in results]
    
    # BM25 requires the text to be split into individual words
    tokenized_corpus = [doc["text"].lower().split(" ") for doc in results]
    bm25_index = BM25Okapi(tokenized_corpus)

def keyword_search(query: str, n_results: int = 15):
    """Searches using exact keyword matching (BM25)."""
    if bm25_index is None:
        return []
        
    tokenized_query = query.lower().split(" ")
    top_results = bm25_index.get_top_n(tokenized_query, all_chunks_cache, n=n_results)
    
    formatted_results = []
    for res in top_results:
        formatted_results.append({
            "text": res["text"],
            "source": res["metadata"].get("source", "Unknown"),
            "page": res["metadata"].get("page", "Unknown")
        })
        
    return formatted_results


# ─────────────────────────────────────────────────────────────
# VECTOR SEARCH
# ─────────────────────────────────────────────────────────────
async def search_db(query: str, n_results: int = 5):
    """
    Takes a user's question, converts it to a vector, 
    and uses MongoDB Atlas Vector Search.
    """
    # 1. Embed the user's query
    query_vector = embedding_model.encode([query])[0].tolist()
    
    # 2. Run Atlas Vector Search
    # Note: This requires a vector index named 'vector_index' in Atlas
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": n_results
            }
        },
        {
            "$project": {
                "_id": 0,
                "text": 1,
                "source": 1,
                "page": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    try:
        cursor = db.chunks.aggregate(pipeline)
        results = await cursor.to_list(length=n_results)
        
        # Format the results
        retrieved_chunks = []
        for doc in results:
            retrieved_chunks.append({
                "text": doc["text"],
                "source": doc.get("source", "Unknown"),
                "page": doc.get("page", "Unknown"),
                "distance": 1.0 - doc.get("score", 1.0) # Convert similarity to distance
            })
            
        return retrieved_chunks
    except Exception as e:
        print(f"⚠️ Vector search failed (did you create the Atlas index?): {e}")
        # Fallback to empty if Atlas vector search isn't configured yet
        return []


# ─────────────────────────────────────────────────────────────
# HYBRID RETRIEVAL
# ─────────────────────────────────────────────────────────────
async def retrieve_and_rerank(query: str, top_k_initial: int = 15, top_k_final: int = 4):
    """Hybrid Search + Reranking Pipeline"""
    
    # 1. Semantic Search (MongoDB Atlas)
    semantic_results = await search_db(query, n_results=top_k_initial)
    
    # 2. Keyword Search (BM25)
    bm25_results = keyword_search(query, n_results=top_k_initial)
    
    # 3. Combine them and remove duplicates
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


# ─────────────────────────────────────────────────────────────
# TASK MODE HELPER
# ─────────────────────────────────────────────────────────────
async def get_chunks_for_file(filename: str, max_chunks: int = 10) -> list[str]:
    """Bypasses vector search. Used for Summarize, Quiz, Flashcards."""
    cursor = db.chunks.find({"source": filename}, {"text": 1}).limit(max_chunks)
    results = await cursor.to_list(length=max_chunks)
    return [doc["text"] for doc in results]
