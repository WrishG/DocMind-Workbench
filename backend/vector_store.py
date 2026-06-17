from rank_bm25 import BM25Okapi
from database import db
import asyncio
from llm import generate_embeddings

# ─────────────────────────────────────────────────────────────
# DATABASE INSERTION
# ─────────────────────────────────────────────────────────────
async def add_chunks_to_db(filename: str, chunks: list[dict]):
    """Takes chunk dictionaries, embeds the text using Gemini, and saves to MongoDB."""
    
    # Generate embeddings via API (ZERO local memory usage!)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    
    # Prepare documents for MongoDB
    db_documents = []
    for i, chunk in enumerate(chunks):
        db_documents.append({
            "source": filename,
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": embeddings[i] # 768-dimension Gemini vector!
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
    print(f"✅ BM25 Index rebuilt with {len(results)} chunks.")

def keyword_search(query: str, n_results: int = 4):
    """Searches the BM25 index for keyword matches."""
    if bm25_index is None or not all_chunks_cache:
        return []
        
    # Get the raw scores for all documents
    tokenized_query = query.lower().split(" ")
    scores = bm25_index.get_scores(tokenized_query)
    
    # Sort and get top N
    top_n_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
    
    retrieved_chunks = []
    for i in top_n_indices:
        if scores[i] > 0: # Only include chunks that actually matched a keyword
            chunk_data = all_chunks_cache[i]
            retrieved_chunks.append({
                "text": chunk_data["text"],
                "source": chunk_data["metadata"].get("source", "Unknown"),
                "page": chunk_data["metadata"].get("page", "Unknown"),
                "score": float(scores[i])
            })
            
    return retrieved_chunks


# ─────────────────────────────────────────────────────────────
# VECTOR SEARCH (MongoDB Atlas)
# ─────────────────────────────────────────────────────────────
async def search_db(query: str, n_results: int = 4):
    """Performs Semantic Search using MongoDB Atlas Vector Search."""
    
    # Generate the query embedding using Gemini
    query_embedding = generate_embeddings([query])[0]
    
    # Build the MongoDB Atlas Vector Search Pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
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
# HYBRID RETRIEVAL & RERANKING (RRF)
# ─────────────────────────────────────────────────────────────
def compute_rrf(rank: int, k: int = 60) -> float:
    """Computes the Reciprocal Rank Fusion score."""
    return 1.0 / (k + rank)

async def retrieve_and_rerank(query: str, top_k_initial: int = 15, top_k_final: int = 4):
    """Hybrid Search using Reciprocal Rank Fusion (Zero Memory Overhead)"""
    
    # 1. Semantic Search (MongoDB Atlas)
    semantic_results = await search_db(query, n_results=top_k_initial)
    
    # 2. Keyword Search (BM25)
    bm25_results = keyword_search(query, n_results=top_k_initial)
    
    # 3. Reciprocal Rank Fusion
    rrf_scores = {}
    chunk_data = {}
    
    # Process Semantic Results
    for rank, chunk in enumerate(semantic_results):
        text = chunk["text"]
        chunk_data[text] = chunk
        rrf_scores[text] = rrf_scores.get(text, 0.0) + compute_rrf(rank + 1)
        
    # Process BM25 Results
    for rank, chunk in enumerate(bm25_results):
        text = chunk["text"]
        chunk_data[text] = chunk
        rrf_scores[text] = rrf_scores.get(text, 0.0) + compute_rrf(rank + 1)
        
    # 4. Sort by final RRF score
    sorted_chunks = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)
    
    final_results = []
    for text in sorted_chunks[:top_k_final]:
        chunk = chunk_data[text]
        chunk["rerank_score"] = rrf_scores[text]
        final_results.append(chunk)
        
    return final_results


# ─────────────────────────────────────────────────────────────
# TASK MODE HELPER
# ─────────────────────────────────────────────────────────────
async def get_chunks_for_file(filename: str, max_chunks: int = 10) -> list[str]:
    """Bypasses vector search. Used for Summarize, Quiz, Flashcards."""
    cursor = db.chunks.find({"source": filename}, {"text": 1}).limit(max_chunks)
    results = await cursor.to_list(length=max_chunks)
    return [doc["text"] for doc in results]
