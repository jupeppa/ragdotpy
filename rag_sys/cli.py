import os
import sys
import logging
from dotenv import load_dotenv

from rag_sys.interactive import InteractiveRAG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_sys.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the interactive RAG system"""
    load_dotenv()

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set the GOOGLE_API_KEY environment variable")
        sys.exit(1)
    
    # Check for default documents path
    default_docs_path = os.getenv("RAG_DOCS_PATH")
    
    # Start interactive session
    try:
        interactive_rag = InteractiveRAG(api_key, default_docs_path)
        interactive_rag.cmdloop()
    except Exception as e:
        logger.error(f"Error starting interactive session: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()