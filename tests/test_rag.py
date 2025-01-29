import unittest
import os
from datetime import datetime

from rag_sys.rag import RAGSystem, DocumentInfo
from rag_sys.document_parser import DocumentParser
from rag_sys.text_chunker import TextChunker


# Mock class for embedding, to avoid API usage during tests
class MockEmbeddingFunction:
    def __init__(self, api_key, document_mode=True):
        pass

    def __call__(self, input):
        return [[1.0, 2.0, 3.0] for _ in input]

class TestRAGSystem(unittest.TestCase):

    def setUp(self):
        # Set up basic env variables (just for the mock embedding)
        os.environ["GOOGLE_API_KEY"] = "test_api_key"

        self.rag = RAGSystem(api_key="test_api_key", db_name="test_db")  # using mock embedding
        self.rag.embed_fn = MockEmbeddingFunction(api_key="test_api_key")

        # Create sample document for testing purposes
        self.test_file = "test_file.txt"
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("This is a test document for RAG System tests.\n")
            f.write("It includes some text that is used for the testing of chunking, embedding and document processing.\n")
        
    def tearDown(self):
        #Clean up the test file if it exists
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        
        # Clean up test Chroma database if it exists (not available via the API, this is a workaround)
        if os.path.exists("test_db"):
            import shutil
            shutil.rmtree("test_db")
    
    def test_document_parsing(self):
        parser = DocumentParser()
        
        # Test parsing text
        with open(self.test_file, 'r') as f:
            expected_text = f.read()
        
        parsed_text = parser.read_txt(self.test_file)
        self.assertEqual(parsed_text, expected_text)

    def test_text_chunking(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "This is a long string of text that needs to be split into smaller chunks."
        chunks = chunker.chunk_text(text)
        self.assertTrue(len(chunks) > 1)  # Text should be chunked
        self.assertTrue(all(len(chunk) <= 50 for chunk in chunks)) #Ensure every chunk is smaller that set max
    
    def test_process_file(self):
        # Process the test file
        chunk_ids = self.rag.process_file(self.test_file)
        self.assertTrue(chunk_ids)
        self.assertIn(self.test_file, self.rag.document_info)
        self.assertIn(self.test_file, self.rag.document_tracker.document_cache)

    def test_query(self):
        # Process the test file first
        self.rag.process_file(self.test_file)
        
        # Query some text
        query_text = "test"
        results = self.rag.query(query_text, n_results=1)
        self.assertTrue(len(results["results"]) > 0)  # Ensure some results are returned

    def test_remove_document(self):
        self.rag.process_file(self.test_file)  # first, add the file
        self.rag.remove_document(self.test_file)
        self.assertNotIn(self.test_file, self.rag.document_info)
        self.assertNotIn(self.test_file, self.rag.document_tracker.document_cache)

if __name__ == '__main__':
    unittest.main()