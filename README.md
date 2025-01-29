# Interactive RAG System

This is an interactive Retrieval-Augmented Generation (RAG) system that allows you to process documents, ask questions, and manage conversations.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd rag_sys
    ```

2.  **Create a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    *   Create a `.env` file in the root directory.
    *   Add your Google API key and the desired directory for documents

        ```env
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        RAG_DOCS_PATH="./data/" # Or any other path to the docs
        ```

## Usage

1.  **Run the interactive RAG system:**

    ```bash
    python -m rag_sys.cli
    ```

    This will start the interactive command-line interface.

2.  **Basic commands:**

    *   `ask <question>`: Ask a question.
    *   `process <directory>`: Process documents in a directory.
    *   `list [page_number]`: List conversations.
    *   `new [title]`: Start a new conversation.
    *   `load <id>`: Load a conversation by ID.
    *   `search <text>`: Search conversations.
    *   `stats`: Show system statistics.
    *   `sources`: Show document sources
    *   `history`: Show current conversation history.
    *   `help [command]`: Show help for commands.
    *   `exit` or `quit`: Exit the application.

## Example

    [RAG]> process ./data
    [RAG]> ask What is this about?
    [RAG]> list

    
## Tests

    You can run the tests with:
    ```bash
    python -m unittest tests/test_rag.py