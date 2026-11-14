import hashlib
import math
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

COLLECTION_NAME = "candidate_resumes"
VECTOR_DIM = 64  # Lightweight deterministic embedding dimension for local zero-API-key execution

# Initialize Qdrant in persistent local disk mode (Zero Docker setup required for MVP)
qdrant_client = QdrantClient(path="./qdrant_storage")

def init_vector_store():
    """Creates the Qdrant vector collection on startup if it does not already exist."""
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )

def text_to_deterministic_vector(text: str) -> List[float]:
    """
    Converts resume or job description text into a normalized 64-dimensional vector
    using token hashing (can be swapped with OpenAI/FastEmbed embeddings in production).
    """
    vec = [0.0] * VECTOR_DIM
    tokens = text.lower().split()
    if not tokens:
        return vec

    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % VECTOR_DIM
        vec[idx] += 1.0

    # L2 Normalize for Cosine Similarity
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]

def index_candidate_resume(candidate_id: str, anonymized_id: str, job_id: str, scrubbed_text: str, skills: List[str]):
    """Upserts the candidate's anonymized resume vector and metadata payload into Qdrant."""
    init_vector_store()
    vector = text_to_deterministic_vector(scrubbed_text + " " + " ".join(skills))
    
    # Generate deterministic integer/UUID point ID from candidate_id
    point_id = int(hashlib.md5(candidate_id.encode("utf-8")).hexdigest()[:12], 16)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "candidate_id": candidate_id,
                    "anonymized_id": anonymized_id,
                    "job_id": job_id,
                    "extracted_skills": skills,
                    "resume_snippet": scrubbed_text[:300]
                }
            )
        ]
    )

def semantic_search_candidates(query_text: str, limit: int = 5) -> List[Dict]:
    """Searches Qdrant for candidates semantically matching a natural language query."""
    init_vector_store()
    query_vector = text_to_deterministic_vector(query_text)
    
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    ).points

    return [
        {
            "candidate_id": hit.payload.get("candidate_id"),
            "anonymized_id": hit.payload.get("anonymized_id"),
            "job_id": hit.payload.get("job_id"),
            "similarity_score": round(hit.score * 100, 2),
            "skills": hit.payload.get("extracted_skills", []),
            "snippet": hit.payload.get("resume_snippet", "")
        }
        for hit in results
    ]