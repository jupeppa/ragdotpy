from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import google.generativeai as genai
import logging
import chromadb

from rag_sys.text_chunker import TextChunker
from rag_sys.embedding import GeminiEmbeddingFunction
from rag_sys.document_parser import DocumentParser
from rag_sys.document_tracker import DocumentTracker

import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Store metadata about processed documents"""
    file_path: str
    file_type: str
    size: int
    processed_date: datetime
    chunks: int
    embedding_model: str

class RAGSystem:
    """Main RAG system class with document tracking and generation capabilities"""
    
    def __init__(self, api_key: str, db_name: str = "documentdb"):
        self.api_key = api_key
        self.db_name = db_name
        self.embed_fn = GeminiEmbeddingFunction(api_key)
        self.chunker = TextChunker()
        self.document_info: Dict[str, DocumentInfo] = {}
        self.document_tracker = DocumentTracker()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient()
        self.db = self.chroma_client.get_or_create_collection(
            name=db_name,
            embedding_function=self.embed_fn
        )
        
        logger.info(f"RAG System initialized with database: {db_name}")

    def process_directory(self, directory_path: str, file_types: Optional[List[str]] = None) -> None:
        """Process all supported documents in a directory"""
        if file_types is None:
            file_types = ['.pdf', '.docx', '.txt', '.html']
            
        directory = Path(directory_path)
        processed_files = set()
        
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in file_types:
                str_path = str(file_path)
                try:
                    # Skip if already processed and unchanged
                    if self.document_tracker.is_document_processed(str_path):
                        logger.info(f"Skipping already processed file: {str_path}")
                        chunk_ids = self.document_tracker.get_chunk_ids(str_path)
                        processed_files.update(chunk_ids)
                        continue
                        
                    # Process new or modified file
                    chunk_ids = self.process_file(str_path)
                    processed_files.update(chunk_ids)
                    
                except Exception as e:
                    logger.error(f"Failed to process {str_path}: {e}")

        # Clean up old chunks that no longer exist
        self._cleanup_old_chunks(processed_files)

    def process_file(self, file_path: str) -> List[str]:
        """Process a single file and return chunk IDs"""
        file_type = Path(file_path).suffix.lower()
        
        parser_methods = {
            '.pdf': DocumentParser.read_pdf,
            '.docx': DocumentParser.read_docx,
            '.txt': DocumentParser.read_txt,
            '.html': DocumentParser.read_html
        }
        
        if file_type not in parser_methods:
            logger.warning(f"Unsupported file type: {file_type}")
            return []
            
        try:
            text = parser_methods[file_type](file_path)
            chunks = self.chunker.chunk_text(text)
            
            # Generate unique IDs for chunks
            chunk_ids = [f"{Path(file_path).stem}_chunk_{i}" for i in range(len(chunks))]
            
            # Add to ChromaDB
            self.db.add(
                documents=chunks,
                ids=chunk_ids,
                metadatas=[{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
            )
            
            # Store document info
            self.document_info[file_path] = DocumentInfo(
                file_path=file_path,
                file_type=file_type,
                size=len(text),
                processed_date=datetime.now(),
                chunks=len(chunks),
                embedding_model="models/text-embedding-004"
            )
            
            # Update document tracker
            self.document_tracker.add_document(file_path, chunk_ids)
            
            logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks created")
            
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise

    def _cleanup_old_chunks(self, current_chunk_ids: Set[str]) -> None:
        """Remove chunks that no longer exist in the current document set"""
        try:
            existing_chunks = set(self.db.get(include=['documents'])['ids'])
            chunks_to_remove = existing_chunks - current_chunk_ids
            
            if chunks_to_remove:
                self.db.delete(ids=list(chunks_to_remove))
                logger.info(f"Removed {len(chunks_to_remove)} obsolete chunks")
        except Exception as e:
            logger.error(f"Error during chunk cleanup: {e}")

    def remove_document(self, file_path: str) -> None:
        """Remove a document and its chunks from the system"""
        try:
            chunk_ids = self.document_tracker.get_chunk_ids(file_path)
            if chunk_ids:
                self.db.delete(ids=chunk_ids)
            self.document_tracker.remove_document(file_path)
            if file_path in self.document_info:
                del self.document_info[file_path]
            logger.info(f"Successfully removed document: {file_path}")
        except Exception as e:
            logger.error(f"Error removing document {file_path}: {e}")

    def query(self, query_text: str, n_results: int = 3) -> Dict:
        """Query the document database"""
        try:
            # Switch to query mode for embedding
            self.embed_fn.document_mode = False
            
            # Search the database
            results = self.db.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            return {
                "query": query_text,
                "results": [
                    {
                        "text": doc,
                        "metadata": meta,
                        "similarity": 1 - dist  # Convert distance to similarity
                    }
                    for doc, meta, dist in zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )
                ]
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def generate_response(self, query: str, language: str = "en",
                         model_name: str = "gemini-2.0-flash-exp",
                         context_history: Optional[List[Dict]] = None,
                         retrieval_enabled: bool = True) -> str:
        """Generate a response using retrieved documents and conversation history"""
        try:
            context_parts = []
            
            # Only perform retrieval if enabled
            if retrieval_enabled:
                retrieved_docs = self.query(query, 10)
                for result in retrieved_docs["results"]:
                    source = result["metadata"]["source"]
                    text = result["text"]
                    context_parts.append(f"From {source}:\n{text}")
            
            reference_context = "\n\n".join(context_parts)
            
            # Create conversation context
            conversation_context = ""
            if context_history:
                conversation_pairs = []
                for i in range(0, len(context_history)-1, 2):
                    user_msg = context_history[i]["content"]
                    assistant_msg = context_history[i+1]["content"]
                    conversation_pairs.append(
                        f"User: {user_msg}\nAssistant: {assistant_msg}"
                    )
                conversation_context = "\n\n".join(conversation_pairs)
            
            # Adjust prompt based on whether this is a summary or full response
            if not retrieval_enabled:
                prompt = f"""Based on the conversation history below, provide a brief 1-2 sentence summary.
                Answer in the specified language: {language}
                
                Conversation:
                {conversation_context}
                """
            else:
                prompt = f"""You are a helpful and informative bot that answers questions using the reference passages and conversation history included below.
                Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.
                If the passages are irrelevant to the answer, you may ignore them. Answer in the specified language: {language}
                
                Previous Conversation:
                {conversation_context}
                
                Reference Passages:
                {reference_context}
                
                Current Question: {query}
                """
            
            # Generate response
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise

    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        stats = {
            "total_documents": len(self.document_info),
            "total_chunks": sum(doc.chunks for doc in self.document_info.values()),
            "document_types": dict(pd.Series([doc.file_type for doc in self.document_info.values()]).value_counts()),
            "average_chunks_per_doc": sum(doc.chunks for doc in self.document_info.values()) / len(self.document_info) if self.document_info else 0,
            "processed_documents": list(self.document_info.keys())
        }
        
        # Add document tracking stats
        stats.update({
            "cached_documents": len(self.document_tracker.document_cache),
            "last_processed": max([info.get('last_processed', '1970-01-01') 
                                 for info in self.document_tracker.document_cache.values()],
                                default='No documents processed')
        })
        
        return stats

    def get_document_sources(self) -> Dict[str, List[str]]:
        """Get a mapping of which documents contributed to which chunks"""
        try:
            all_metadatas = self.db.get(include=['metadatas'])['metadatas']
            sources = {}
            for metadata in all_metadatas:
                source = metadata['source']
                if source not in sources:
                    sources[source] = []
                sources[source].append(f"Chunk {metadata['chunk_index']}")
            return sources
        except Exception as e:
            logger.error(f"Error getting document sources: {e}")
            return {}