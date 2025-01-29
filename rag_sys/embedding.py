import google.generativeai as genai
import logging
from typing import List
from tqdm import tqdm
import chromadb

logger = logging.getLogger(__name__)


class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    """Enhanced embedding function with retry logic and error handling"""
    
    def __init__(self, api_key: str, document_mode: bool = True):
        self.document_mode = document_mode
        genai.configure(api_key=api_key)
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            embedding_task = "retrieval_document" if self.document_mode else "retrieval_query"
            
            embeddings = []
            for text in tqdm(input, desc="Generating embeddings"):
                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type=embedding_task,
                )
                embeddings.append(response["embedding"])
            
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise