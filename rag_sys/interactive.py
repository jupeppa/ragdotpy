import cmd
import os
import signal
import sys
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from dotenv import load_dotenv


from rag_sys.rag import RAGSystem, DocumentInfo
from rag_sys.conversation import ConversationStore

logger = logging.getLogger(__name__)

class InteractiveRAG(cmd.Cmd):
    """Interactive command line interface for RAG system"""
    
    intro = """
    Ласкаво просимо до Інтерактивної RAG Системи!
    
    Основні команди:
    - ask <питання>     - поставити питання системі
    - process <папка>   - обробити документи з вказаної папки
    - list              - показати список розмов
    - new [назва]       - почати нову розмову
    - load <id>         - завантажити розмову за ID
    - search <текст>    - пошук по розмовам
    - stats             - показати статистику системи
    - sources           - показати джерела документів
    - history           - показати історію поточної розмови
    - help              - побачити всі доступні команди
    
    Введіть 'help <команда>' для детальної інформації про команду.
    Введіть 'exit' або 'quit' для виходу.
    """
    
    prompt = '\n[RAG]> '
    
    def __init__(self, api_key: str, default_docs_path: Optional[str] = None):
        super().__init__()
        self.console = Console()
        self.rag = RAGSystem(api_key=api_key)
        self.conversation_store = ConversationStore()
        self.current_conversation_id = None
        self.conversation_history = []
        self.last_query = None
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self.handle_sigint)

        # Process documents from default path if provided
        if default_docs_path:
            self._init_document_processing(default_docs_path)
        else:
            # Try to find documents in cache
            self._process_cached_documents()

    def _process_cached_documents(self):
        """Process any documents that exist in cache but haven't been processed"""
        try:
            cached_docs = self.rag.document_tracker.document_cache
            if not cached_docs:
                return

            docs_to_process = []
            for doc_path in cached_docs.keys():
                if os.path.exists(doc_path) and not self.rag.document_tracker.is_document_processed(doc_path):
                    docs_to_process.append(doc_path)
                    
            if docs_to_process:
                self.console.print("[yellow]Знайдено непроіндексовані документи у кеші. Починаю обробку...[/yellow]")
                for doc_path in docs_to_process:
                    try:
                        self.rag.process_file(doc_path)
                        self.console.print(f"[green]Оброблено: {doc_path}[/green]")
                    except Exception as e:
                        self.console.print(f"[red]Помилка обробки {doc_path}: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Помилка обробки кешованих документів: {e}[/red]")

    def _init_document_processing(self, docs_path: str):
        """Initialize document processing from a directory"""
        if not os.path.exists(docs_path):
            self.console.print(f"[red]Папка не існує: {docs_path}[/red]")
            return

        try:
            self.console.print(f"[yellow]Ініціалізація документів з {docs_path}...[/yellow]")
            self.rag.process_directory(docs_path)
            self.console.print("[green]Ініціалізація документів завершена![/green]")
        except Exception as e:
            self.console.print(f"[red]Помилка ініціалізації документів: {e}[/red]")

    def get_names(self) -> List[str]:
        """Return list of command names for autocomplete"""
        return ['ask', 'process', 'list', 'new', 'load', 'search', 
                'stats', 'sources', 'history', 'exit', 'quit', 'help']
    
    def do_help(self, arg: str):
        """List available commands or provide help for a specific command"""
        if arg:
            # Get the help method for the command
            try:
                func = getattr(self, 'help_' + arg)
                help_text = func()
                if help_text:
                    self.console.print(Panel(help_text, title=f"Допомога: {arg}", border_style="blue"))
                else:
                    self.console.print(f"[yellow]Немає додаткової інформації для команди: {arg}[/yellow]")
            except AttributeError:
                self.console.print(f"[red]Невідома команда: {arg}[/red]")
        else:
            # Show general help with all commands
            commands = {
                'ask': 'Поставити питання системі',
                'process': 'Обробити документи з вказаної папки',
                'list': 'Показати список розмов',
                'new': 'Почати нову розмову',
                'load': 'Завантажити розмову за ID',
                'search': 'Пошук по розмовам',
                'stats': 'Показати статистику системи',
                'sources': 'Показати джерела документів',
                'history': 'Показати історію поточної розмови',
                'exit/quit': 'Вийти з програми'
            }
            
            table = Table(title="Доступні Команди")
            table.add_column("Команда", style="cyan")
            table.add_column("Опис", style="green")
            
            for cmd, desc in commands.items():
                table.add_row(cmd, desc)
            
            self.console.print(table)

    def help_ask(self):
        """Help for ask command"""
        return """
        ask <питання>
        Поставити питання системі, використовуючи знання з оброблених документів.
        Приклад: ask що таке машинне навчання?
        """

    def help_process(self):
        """Help for process command"""
        return """
        process <шлях_до_папки>
        Обробити всі підтримувані документи (.pdf, .docx, .txt, .html) у вказаній папці.
        Приклад: process /шлях/до/документів
        """

    def help_new(self):
        """Help for new command"""
        return """
        new [назва]
        Створити нову розмову з опціональною назвою.
        Приклад: new Питання про Python
        """

    def help_list(self):
        """Help for list command"""
        return """
        list [номер_сторінки]
        Показати список останніх розмов. 10 розмов на сторінку.
        Приклад: list 2
        """

    def help_load(self):
        """Help for load command"""
        return """
        load <id>
        Завантажити конкретну розмову за її ID.
        Приклад: load 5
        """

    def help_search(self):
        """Help for search command"""
        return """
        search <запит>
        Пошук по всім розмовам (заголовки, вміст, підсумки).
        Приклад: search python
        """

    def help_stats(self):
        """Help for stats command"""
        return """
        stats
        Показати статистику системи: кількість документів, чанків, типи файлів тощо.
        """

    def help_sources(self):
        """Help for sources command"""
        return """
        sources
        Показати список оброблених документів та їх чанків.
        """

    def help_history(self):
        """Help for history command"""
        return """
        history
        Показати історію поточної розмови.
        """

    def do_stats(self, arg):
        """Show system statistics"""
        try:
            # First, ensure all document info is loaded from cache
            cached_docs = self.rag.document_tracker.document_cache
            for doc_path, info in cached_docs.items():
                if doc_path not in self.rag.document_info and os.path.exists(doc_path):
                    try:
                        file_type = Path(doc_path).suffix.lower()
                        self.rag.document_info[doc_path] = DocumentInfo(
                            file_path=doc_path,
                            file_type=file_type,
                            size=os.path.getsize(doc_path),
                            processed_date=datetime.fromisoformat(info['last_processed']),
                            chunks=len(info['chunk_ids']),
                            embedding_model="models/text-embedding-004"
                        )
                    except Exception as e:
                        logger.error(f"Error loading document info for {doc_path}: {e}")
            
            stats = self.rag.get_system_stats()
            
            table = Table(title="Статистика Системи")
            table.add_column("Метрика", style="cyan")
            table.add_column("Значення", style="magenta")
            
            # Transform keys to Ukrainian
            ukr_keys = {
                "total_documents": "Всього документів",
                "total_chunks": "Всього чанків",
                "document_types": "Типи документів",
                "average_chunks_per_doc": "Середня к-сть чанків на документ",
                "processed_documents": "Оброблені документи",
                "cached_documents": "Документи в кеші",
                "last_processed": "Останній оброблений"
            }
            
            for key, value in stats.items():
                if isinstance(value, (list, dict)):
                    value = str(value)
                table.add_row(ukr_keys.get(key, key), str(value))
                
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Помилка отримання статистики: {e}[/red]")
    
    def handle_sigint(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\nUse 'exit' or 'quit' to exit properly.")
        return

    def do_process(self, arg):
        """Process documents from a directory: process <directory_path>"""
        if not arg:
            self.console.print("[red]Please provide a directory path[/red]")
            return
            
        try:
            self.console.print(f"[yellow]Processing documents in {arg}...[/yellow]")
            self.rag.process_directory(arg)
            self.console.print("[green]Processing complete![/green]")
        except Exception as e:
            self.console.print(f"[red]Error processing directory: {e}[/red]")

    def _ensure_conversation(self):
        """Ensure there's an active conversation"""
        if self.current_conversation_id is None:
            title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.current_conversation_id = self.conversation_store.create_conversation(title)
            self.conversation_history = []

    def _update_current_conversation(self):
        """Update the current conversation in storage"""
        if self.current_conversation_id:
            summary = ""
            if self.conversation_history:
                try:
                    # Generate summary without retrieval
                    summary = self.rag.generate_response(
                        query="",  # Not used when retrieval_enabled=False
                        language="Ukrainian",
                        model_name="gemini-1.5-flash-latest",
                        context_history=self.conversation_history,
                        retrieval_enabled=False  # Skip vector search for summary
                    )
                except Exception as e:
                    logger.error(f"Error generating summary: {e}")
                    summary = "No summary available"

            self.conversation_store.update_conversation(
                self.current_conversation_id,
                self.conversation_history,
                summary
            )

    def do_new(self, arg):
        """Start a new conversation: new [title]"""
        title = arg if arg else f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.current_conversation_id = self.conversation_store.create_conversation(title)
        self.conversation_history = []
        self.console.print(f"[green]Started new conversation: {title}[/green]")

    def do_list(self, arg):
        """List recent conversations: list [page_number]"""
        try:
            page = int(arg) if arg else 1
            offset = (page - 1) * 10
            conversations = self.conversation_store.list_conversations(limit=10, offset=offset)
            
            if not conversations:
                self.console.print("[yellow]No conversations found[/yellow]")
                return
                
            table = Table(title=f"Conversations (Page {page})")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Last Updated", style="green")
            table.add_column("Summary", style="white")
            
            for conv in conversations:
                table.add_row(
                    str(conv[0]),
                    conv[1],
                    conv[2].strftime("%Y-%m-%d %H:%M"),
                    str(conv[3])
                )
                
            self.console.print(table)
            
        except ValueError:
            self.console.print("[red]Invalid page number[/red]")
    
    def do_load(self, arg):
        """Load a specific conversation: load <conversation_id>"""
        try:
            conv_id = int(arg)
            conversation = self.conversation_store.get_conversation(conv_id)
            
            if conversation:
                self.current_conversation_id = conversation.id
                self.conversation_history = conversation.messages
                self.console.print(f"[green]Loaded conversation: {conversation.title}[/green]")
                self.do_history("")
            else:
                self.console.print("[red]Conversation not found[/red]")
                
        except ValueError:
            self.console.print("[red]Invalid conversation ID[/red]")

    def do_search(self, arg):
        """Search conversations: search <query>"""
        if not arg:
            self.console.print("[red]Please provide a search query[/red]")
            return
            
        results = self.conversation_store.search_conversations(arg)
        
        if not results:
            self.console.print("[yellow]No matching conversations found[/yellow]")
            return
            
        table = Table(title=f"Search Results for: {arg}")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Last Updated", style="green")
        table.add_column("Summary", style="white")
        
        for result in results:
            table.add_row(
                str(result[0]),
                result[1],
                result[2].strftime("%Y-%m-%d %H:%M"),
                str(result[3])
            )
            
        self.console.print(table)

    def do_ask(self, arg):
        """Ask a question: ask <your question>"""
        if not arg:
            self.console.print("[red]Please provide a question[/red]")
            return
            
        try:
            # Ensure we have an active conversation
            self._ensure_conversation()
            
            # Store query in history
            self.last_query = arg
            self.conversation_history.append({"role": "user", "content": arg})
            
            # Generate response
            response = self.rag.generate_response(
                arg,
                language="Ukrainian",
                context_history=self.conversation_history
            )
            
            # Store response in history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Update conversation in database
            self._update_current_conversation()
            
            # Display response
            rprint(Panel(response, title="Response", border_style="green"))
            
        except Exception as e:
            self.console.print(f"[red]Error generating response: {e}[/red]")

    def do_summary(self, arg):
        """Show summary of current conversation"""
        if not self.current_conversation_id:
            self.console.print("[yellow]No active conversation[/yellow]")
            return
            
        conversation = self.conversation_store.get_conversation(self.current_conversation_id)
        if conversation and conversation.summary:
            rprint(Panel(conversation.summary, title="Conversation Summary", border_style="blue"))
        else:
            self.console.print("[yellow]No summary available[/yellow]")

    def do_sources(self, arg):
        """Show document sources"""
        try:
            sources = self.rag.get_document_sources()
            
            table = Table(title="Document Sources")
            table.add_column("Document", style="cyan")
            table.add_column("Chunks", style="magenta")
            
            for doc, chunks in sources.items():
                table.add_row(doc, str(len(chunks)))
                
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting sources: {e}[/red]")

    def do_history(self, arg):
        """Show conversation history"""
        if not self.conversation_history:
            self.console.print("[yellow]No conversation history yet[/yellow]")
            return
            
        for i, entry in enumerate(self.conversation_history, 1):
            role = entry["role"]
            content = entry["content"]
            color = "cyan" if role == "user" else "green"
            rprint(Panel(content, title=f"{i}. {role.capitalize()}", border_style=color))

    def do_clear_history(self, arg):
        """Clear conversation history"""
        self.conversation_history = []
        self.console.print("[yellow]Conversation history cleared[/yellow]")

    def do_remove(self, arg):
        """Remove a document: remove <file_path>"""
        if not arg:
            self.console.print("[red]Please provide a file path[/red]")
            return
            
        try:
            self.rag.remove_document(arg)
            self.console.print(f"[green]Successfully removed document: {arg}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error removing document: {e}[/red]")

    def do_exit(self, arg):
        """Exit the program"""
        self.console.print("[yellow]Goodbye![/yellow]")
        return True
        
    def do_quit(self, arg):
        """Exit the program"""
        return self.do_exit(arg)

    def default(self, line):
        """Handle unknown commands"""
        self.console.print(f"[red]Unknown command: {line}[/red]")
        self.console.print("Type 'help' or '?' to see available commands")