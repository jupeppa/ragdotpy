import logging
from typing import List

logger = logging.getLogger(__name__)

class TextChunker:
    """Split documents into chunks for better embedding"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text (str): The input text to be chunked
            
        Returns:
            List[str]: List of text chunks
            
        Example:
            chunker = TextChunker(chunk_size=100, overlap=20)
            chunks = chunker.chunk_text("long text here...")
        """
        chunks = []
        if not text:
            return chunks

        # Ensure overlap is smaller than chunk_size
        if self.overlap >= self.chunk_size:
            self.overlap = self.chunk_size // 2
            logger.warning(f"Overlap was too large, adjusted to {self.overlap}")

        start = 0
        text_length = len(text)

        while start < text_length:
            # Calculate end position for current chunk
            end = min(start + self.chunk_size, text_length)
            
            # Extract chunk
            chunk = text[start:end]
            
            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk)
            
            # Calculate next start position
            # If this is the last chunk, break
            if end == text_length:
                break
                
            # Move start position forward by chunk_size - overlap
            start += (self.chunk_size - self.overlap)
            
            # Safety check: ensure we're making progress
            if start >= end:
                logger.warning("Chunking progress stalled, breaking loop")
                break

        return chunks