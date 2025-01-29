import json
import logging
import hashlib
import os
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class DocumentTracker:
    """Track processed documents to avoid reprocessing"""
    
    def __init__(self, cache_file: str = "document_cache.json"):
        self.cache_file = cache_file
        self.document_cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load document cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache file: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save document cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.document_cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")

    def get_file_hash(self, file_path: str) -> str:
        """Calculate file hash using SHA-256"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""

    def is_document_processed(self, file_path: str) -> bool:
        """Check if document has been processed and hasn't changed"""
        if not os.path.exists(file_path):
            return False

        current_hash = self.get_file_hash(file_path)
        file_info = self.document_cache.get(file_path, {})
        
        return (file_info.get('hash') == current_hash and 
                file_info.get('chunk_ids') is not None)

    def add_document(self, file_path: str, chunk_ids: List[str]) -> None:
        """Add or update document in cache"""
        self.document_cache[file_path] = {
            'hash': self.get_file_hash(file_path),
            'last_processed': datetime.now().isoformat(),
            'chunk_ids': chunk_ids
        }
        self._save_cache()

    def get_chunk_ids(self, file_path: str) -> List[str]:
        """Get chunk IDs for a processed document"""
        return self.document_cache.get(file_path, {}).get('chunk_ids', [])

    def remove_document(self, file_path: str) -> None:
        """Remove document from cache"""
        if file_path in self.document_cache:
            del self.document_cache[file_path]
            self._save_cache()