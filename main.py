from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import sys
import time
import uuid
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure paths
current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root))

# Import modules
from app.chatbot import Chatbot
from app.analytics import log_interaction, get_analytics_summary

# Initialize FastAPI
app = FastAPI()

# Configure directories
static_dir = project_root / "static"
templates_dir = project_root / "templates"
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize components
knowledge_base_path = project_root / "knowledge_base"
os.makedirs(knowledge_base_path, exist_ok=True)
chatbot = None

@app.on_event("startup")
async def startup_event():
    global chatbot
    try:
        chatbot = Chatbot(knowledge_base_path)
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        raise RuntimeError("Chatbot initialization failed")

@app.get("/")
async def home(request: Request):
    """Render chat interface with new session ID"""
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "session_id": str(uuid.uuid4())}
    )

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Handle chat requests with natural responses"""
    try:
        data = await request.json()
        user_input = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not user_input:
            raise HTTPException(status_code=400, detail="Please enter a message")
        if not chatbot:
            raise HTTPException(status_code=503, detail="Service is currently unavailable")
        
        start_time = time.time()
        response, source = chatbot.generate_response(user_input)
        response_time = time.time() - start_time
        
        # Log interaction
        log_interaction(
            session_id=session_id,
            user_input=user_input,
            bot_response=response,
            response_time=response_time,
            document_source=source
        )
        
        return {
            "response": response,
            "session_id": session_id,
            "source": source
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics")
async def get_analytics(days: int = 30):
    """Get analytics data"""
    try:
        return get_analytics_summary(days)
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")
    
@app.post("/api/feedback")
async def submit_feedback(request: Request):
    data = await request.json()
    log_interaction(
        data.get("message"),
        "",  # No bot response needed
        data.get("satisfaction")
    )
    return {"status": "success"}