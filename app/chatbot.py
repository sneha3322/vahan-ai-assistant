from chromadb import Client, Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pathlib import Path
import os
import logging
import re
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self, knowledge_base_path: Path):
        self.conversation_history = []
        self.knowledge_base_path = knowledge_base_path
        self.initialized = False
        
        # Document handlers with detailed responses
        self.document_handlers = {
            'pricing.md': {
                'header': "Pricing Information",
                'format': self._format_pricing,
                'triggers': ["pricing", "plan", "cost", "subscription", "how much"],
                'examples': ["What are your pricing plans?", "How much does Enterprise cost?"]
            },
            'faq.md': {
                'header': "Frequently Asked Questions",
                'format': self._format_faq,
                'triggers': ["faq", "question", "ask", "common queries"],
                'examples': ["Is my data sent to the cloud?", "What languages are supported?"]
            },
            'features.md': {
                'header': "Product Features",
                'format': self._format_features,
                'triggers': ["feature", "capability", "what can", "functionality"],
                'examples': ["What privacy features do you offer?", "Tell me about your processing capabilities"]
            },
            'api.md': {
                'header': "API Documentation",
                'format': self._format_api,
                'triggers': ["api", "endpoint", "curl", "authenticate", "integration"],
                'examples': ["How do I authenticate with the API?", "Show me API examples"]
            }
        }

        try:
            logger.info("Initializing Chatbot...")
            self.embedding_function = SentenceTransformerEmbeddingFunction()
            self.client = Client(Settings(
                persist_directory=str(Path("./chroma_db").absolute()),
                anonymized_telemetry=False
            ))
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                embedding_function=self.embedding_function
            )
            self._load_knowledge_base()
            self.initialized = True
            logger.info("Chatbot initialized successfully")
        except Exception as e:
            logger.error(f"Chatbot initialization failed: {e}")
            raise

    def _load_knowledge_base(self):
        """Load all markdown files into vector database"""
        if not self.knowledge_base_path.exists():
            os.makedirs(self.knowledge_base_path, exist_ok=True)
            logger.warning("Created empty knowledge base directory")
            return

        loaded_files = []
        for file in self.knowledge_base_path.glob("*.md"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        logger.warning(f"Skipped empty file: {file.name}")
                        continue
                        
                    self.collection.add(
                        documents=[content],
                        ids=[file.stem],
                        metadatas=[{"source": file.name}]
                    )
                    loaded_files.append(file.name)
                    logger.info(f"Successfully loaded: {file.name}")
            except Exception as e:
                logger.error(f"Failed to load {file.name}: {e}")

        logger.info(f"Loaded {len(loaded_files)} knowledge documents")

    def generate_response(self, user_input: str) -> Tuple[str, Optional[str]]:
        """Generate detailed responses for user queries"""
        if not self.initialized:
            return "System is initializing... Please try again shortly.", None

        clean_input = user_input.lower().strip()
        self._update_conversation_history("user", clean_input)

        # Handle greetings
        if any(g in clean_input for g in ["hi", "hello", "hey"]):
            return ("Hello! I'm your Vahan AI assistant. I can help you with:\n"
                   "- Product features\n- Pricing information\n- API documentation\n- FAQ\n\n"
                   "What would you like to know about?"), None
        
        # Handle goodbyes
        if any(g in clean_input for g in ["bye", "goodbye"]):
            return ("Goodbye! If you have more questions later, I can help with:\n"
                   "- Technical documentation\n- Pricing plans\n- Troubleshooting\n"
                   "- Feature details\n\nHave a great day!"), None
        
        # Handle help requests
        if "help" in clean_input:
            return self._get_help_response(), None
            
        # Handle unknown person questions
        if any(word in clean_input for word in ["who", "ceo", "founder", "team"]):
            return ("I specialize in product information. For organizational questions:\n"
                   "- Contact support@vahan.ai\n"
                   "- Visit our website's About page\n"
                   "- Check LinkedIn for team information"), None

        # Try direct document matching first
        for doc_name, handler in self.document_handlers.items():
            if any(trigger in clean_input for trigger in handler['triggers']):
                try:
                    doc_content = self.collection.get(ids=[doc_name.split('.')[0]], include=["documents"])['documents'][0]
                    if doc_content:
                        response = handler['format'](doc_content[0])
                        logger.info(f"Found direct match in {doc_name}")
                        return response, doc_name
                except Exception as e:
                    logger.error(f"Error loading {doc_name}: {e}")

        # Fall back to semantic search
        try:
            results = self.collection.query(
                query_texts=[clean_input],
                n_results=1,
                include=["documents", "metadatas"]
            )
            
            if results['documents']:
                content = results['documents'][0][0]
                source = results['metadatas'][0][0]['source']
                logger.info(f"Found semantic match in {source}")
                return self._format_content(content, source), source
            
            logger.warning("No matching document found")
            return self._handle_no_match(clean_input), None

        except Exception as e:
            logger.error(f"Query error: {e}")
            return ("I encountered an error processing your request. Please:\n"
                   "- Try rephrasing your question\n"
                   "- Check our documentation\n"
                   "- Contact support if the problem persists"), None

    def _format_pricing(self, content: str) -> str:
        """Detailed pricing information formatting"""
        table_match = re.search(r'(?s)# Pricing Plans.*?(\|.*?\|\n\|.*?\|\n(\|.*?\|\n)+)', content)
        if table_match:
            table = table_match.group(1)
            # Clean up markdown table formatting
            table = re.sub(r'\|\s*-+\s*\|', '|---------|', table)
            table = re.sub(r'_\w+_\s*', '', table)
            return ("Here are our detailed pricing plans:\n\n" + 
                    table.strip() + 
                    "\n\nAdditional information:\n"
                    "- All plans include local processing\n"
                    "- Volume discounts available\n"
                    "- Annual billing saves 20%\n\n"
                    "Which plan would you like more details about?")
        return ("For comprehensive pricing information:\n"
                "- Visit our pricing page\n"
                "- Contact sales@vahan.ai\n"
                "- Request a custom quote")

    def _format_faq(self, content: str) -> str:
        """Detailed FAQ formatting"""
        qa_pairs = re.findall(r'(?s)\*\*Q: (.*?)\*\*\s*A: (.*?)(?=\n\*\*Q:|\n$)', content)
        if qa_pairs:
            formatted = "Here are detailed answers to common questions:\n\n"
            for i, (question, answer) in enumerate(qa_pairs[:5], 1):
                clean_answer = self._clean_markdown(answer)
                formatted += f"{i}. {question.strip()}\n{clean_answer.strip()}\n\n"
            return (formatted + 
                    "For more FAQs:\n"
                    "- Browse our complete FAQ section\n"
                    "- Search for specific topics\n"
                    "- Contact support for unanswered questions")
        return ("Our FAQ covers important topics like:\n"
                "- Data privacy\n- System requirements\n"
                "- Integration options\n\n"
                "What specific question can I answer for you?")

    def _format_features(self, content: str) -> str:
        """Detailed feature formatting"""
        sections = re.findall(r'(?s)## (.*?)\n(.*?)(?=##|$)', content)
        formatted = "Here's a comprehensive look at our features:\n\n"
        for header, body in sections:
            formatted += f"✦ {header}:\n\n"
            items = re.findall(r'(?m)^\s*-\s*(.*)', body)
            for item in items:
                formatted += f"  • {self._clean_markdown(item)}\n"
            formatted += "\n"
        return (formatted + 
                "Additional capabilities include:\n"
                "- Custom workflow automation\n"
                "- Advanced analytics\n"
                "- Enterprise-grade security\n\n"
                "Which feature would you like more details about?")

    def _format_api(self, content: str) -> str:
        """Detailed API documentation formatting"""
        auth_section = re.search(r'(?s)## Authentication\n(.*?)(?=##|$)', content)
        formatted = "Here's detailed API information:\n\n"
        
        if auth_section:
            auth_content = auth_section.group(1)
            code_blocks = re.findall(r'```(.*?)```', auth_content, re.DOTALL)
            if code_blocks:
                formatted += "Authentication Example:\n```" + code_blocks[0].strip() + "\n```\n\n"
            
            if len(self.conversation_history) >= 2 and "404" in self.conversation_history[-2][1].lower():
                formatted += ("For 404 errors, please verify:\n"
                            "1. Endpoint URL is correct (currently: api.vahan.ai)\n"
                            "2. Your API key is valid and not expired\n"
                            "3. The service is operational (check status.vahan.ai)\n"
                            "4. You're using the correct HTTP method (POST/GET)\n\n")
        
        formatted += ("Additional API resources:\n"
                    "- Full API reference documentation\n"
                    "- Postman collection\n"
                    "- Sample projects on GitHub\n\n"
                    "What specific API question can I answer?")
        return formatted

    def _format_content(self, content: str, source: str) -> str:
        """Format content with detailed responses"""
        handler = self.document_handlers.get(source, {})
        if handler and 'format' in handler:
            return handler['format'](content)
        return self._format_general(content, source)

    def _format_general(self, content: str, source: str = None) -> str:
        """Default detailed formatting"""
        content = self._clean_markdown(content)
        if source:
            return (f"From our {source.replace('.md', '').replace('_', ' ').title()} documentation:\n\n"
                    f"{content}\n\nWould you like more details on any specific aspect?")
        return content

    def _clean_markdown(self, text: str) -> str:
        """Enhanced markdown cleaning"""
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'(?m)^\s*-\s*(.*)', r'• \1', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _get_help_response(self) -> str:
        """Detailed help response"""
        response = ("I can provide detailed information about:\n\n"
                  "✦ Product Features\n"
                  "  - Intelligent processing\n"
                  "  - Privacy controls\n"
                  "  - Productivity tools\n\n"
                  "✦ Pricing Plans\n"
                  "  - Feature comparisons\n"
                  "  - Subscription options\n"
                  "  - Enterprise solutions\n\n"
                  "✦ API Documentation\n"
                  "  - Authentication\n"
                  "  - Endpoints\n"
                  "  - Code examples\n\n"
                  "✦ Frequently Asked Questions\n"
                  "  - Data handling\n"
                  "  - System requirements\n"
                  "  - Common issues\n\n"
                  "What would you like to explore in detail?")
        return response

    def _handle_no_match(self, query: str) -> str:
        """Detailed no-match response"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=3,
                include=["metadatas"]
            )
            if results['metadatas'][0]:
                sources = set(m['source'].replace('.md', '').replace('_', ' ').title() 
                      for m in results['metadatas'][0])
                return ("I couldn't find an exact match. You might explore:\n\n" +
                       "\n".join(f"• {s}" for s in sources) +
                       "\n\nOr ask about:\n"
                       "- Specific features\n"
                       "- Pricing details\n"
                       "- Technical requirements")
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
        
        return self._get_help_response()

    def _update_conversation_history(self, role: str, content: str):
        """Maintain conversation context"""
        self.conversation_history.append((role, content))
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]
