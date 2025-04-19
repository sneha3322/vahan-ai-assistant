# Vahan AI Assistant - Complete Documentation

<div align="center">
  <img src="./static/demo.gif" width="700" alt="Demo">
  <p><em>Document-based chatbot with hybrid search and analytics</em></p>
</div>

## 🔍 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Inline Code Examples](#-inline-code-examples)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

| **Feature**         | **Implementation**                                         |
| ------------------- | ---------------------------------------------------------- |
| Hybrid Search       | Keyword + semantic search (`chatbot.py`)                   |
| Real-time Analytics | SQLite tracking with session history (`analytics.py`)      |
| Self-Healing        | Auto-creates `chroma_db/` and `knowledge_base/` if missing |
| Production Ready    | Uvicorn workers, proper error handling (`main.py`)         |

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

## 🛠 Installation

````bash
# 1. Clone repository
git clone https://github.com/yourusername/Vahan.AI.git
cd Vahan.AI

# 2. Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Launch (development mode)
uvicorn main:app --reload

Expected output:

INFO:     Loading document: api.md...
INFO:     Document embeddings generated
INFO:     Chatbot ready at http://localhost:8000



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



##📡 API Documentation


POST /api/chat

# Request
{
  "message": "What's the Enterprise plan price?"
}

# Response
{
  "response": "Enterprise plan costs $50/month...",
  "source": "pricing.md"
}

GET /api/analytics

# Query Params
?days=7  # Filter timeframe

# Response
{
  "total_queries": 42,
  "avg_response_time": 0.68
}



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



##💻 Inline Code Examples

1. Hybrid Search (chatbot.py)

def generate_response(self, user_input: str) -> Tuple[str, Optional[str]]:
    """Generates responses using:
    1. Direct keyword matching (for FAQs/pricing)
    2. Semantic similarity fallback
    3. Context-aware formatting

    Returns:
        Tuple[formatted_response, source_document]
    """

2. Analytics Tracking (analytics.py)

def log_interaction(session_id: str, user_input: str) -> bool:
    """Logs interactions with:
    - Timestamps (ISO format)
    - Question classification
    - Response times

    Database Schema:
        interactions(
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL
        )
    """



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



##🧪 Testing


# Run all tests
pytest tests/

# Sample test (tests/test_chatbot.py)
def test_pricing_response():
    """Verifies:
    - Correct price extraction
    - Proper table formatting
    - Source attribution
    """


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



##🚨 Troubleshooting

### Common Issues and Solutions:

- **Missing dependencies**
  → Run: `pip install -r requirements.txt --force-reinstall`

- **Port 8000 already in use**
  → Run:
    ```bash
    lsof -i :8000  # Find PID
    kill -9 <PID>  # Replace <PID> with actual process ID
    ```

- **Document load errors**
  → Verify:
    - Files exist in `knowledge_base/` directory
    - User has read permissions (`chmod +r knowledge_base/*.md`)
    - No special characters in filenames

- **Chatbot not initializing**
  → Check:
    - ChromaDB directory exists (`chroma_db/`)
    - No syntax errors in markdown files
    - Sufficient system memory (minimum 2GB RAM)

- **API returning 404 errors**
  → Ensure:
    - Correct endpoint URL (`/api/chat` with POST method)
    - Proper JSON formatting in requests
    - Server is running (`uvicorn main:app --reload`)

<div align="center">
📝 <em>Detailed technical documentation available in each source file</em>
</div>
````
