import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_VERSION = 2
DB_FILE = 'analytics.db'

def init_db():
    """Initialize database with version control and migrations"""
    try:
        is_new_db = not os.path.exists(DB_FILE)
        
        with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
            c = conn.cursor()
            
            # Create version table if needed
            c.execute("""
                CREATE TABLE IF NOT EXISTS version (
                    version INTEGER NOT NULL
                )
            """)
            
            # Get current version or set to 0
            c.execute("SELECT version FROM version LIMIT 1")
            result = c.fetchone()
            current_version = result[0] if result else 0
            
            if is_new_db:
                c.execute("INSERT INTO version (version) VALUES (0)")
                conn.commit()
                logger.info("Created new database")
            
            if current_version < DB_VERSION:
                migrate_db(conn, current_version, DB_VERSION)
                
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def migrate_db(conn, from_version: int, to_version: int):
    """Handle database schema migrations"""
    c = conn.cursor()
    
    try:
        # Version 1 -> 2: Add new columns and indexes
        if from_version < 2:
            c.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    satisfaction INTEGER CHECK(satisfaction BETWEEN 1 AND 5),
                    question_type TEXT NOT NULL,
                    response_time REAL,
                    document_source TEXT
                )
            """)
            
            # Create indexes
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_session 
                ON interactions(session_id)
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_question_type 
                ON interactions(question_type)
            """)
            
            logger.info("Created new tables and indexes")
        
        # Update version
        c.execute("UPDATE version SET version = ?", (to_version,))
        conn.commit()
        logger.info(f"Database upgraded to version {to_version}")
        
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise

def log_interaction(
    session_id: str,
    user_input: str,
    bot_response: str,
    satisfaction: Optional[int] = None,
    response_time: Optional[float] = None,
    document_source: Optional[str] = None
) -> bool:
    """Log interaction with all fields"""
    try:
        question_type = classify_question(user_input)
        
        with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO interactions (
                    timestamp, session_id, user_input, bot_response,
                    satisfaction, question_type, response_time, document_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                user_input,
                bot_response,
                satisfaction,
                question_type,
                response_time,
                document_source
            ))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to log interaction: {e}")
        return False

def classify_question(text: str) -> str:
    """Categorize questions for analytics"""
    text = text.lower()
    if any(w in text for w in ["price", "cost", "plan"]):
        return "pricing"
    elif any(w in text for w in ["how", "setup", "install"]):
        return "setup"
    elif any(w in text for w in ["error", "fix", "bug"]):
        return "troubleshooting"
    elif any(w in text for w in ["api", "integrate", "connect"]):
        return "integration"
    elif any(w in text for w in ["feature", "capability"]):
        return "features"
    return "general"

def get_analytics_summary(days: int = 30) -> Dict:
    """Generate analytics report"""
    try:
        with sqlite3.connect(DB_FILE, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(response_time) as avg_response_time
                FROM interactions
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
            """, (days,))
            metrics = dict(c.fetchone())
            
            c.execute("""
                SELECT 
                    question_type,
                    COUNT(*) as count
                FROM interactions
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY question_type
                ORDER BY count DESC
            """, (days,))
            question_types = [dict(row) for row in c.fetchall()]
            
            return {
                "metrics": metrics,
                "question_types": question_types,
                "time_period": f"Last {days} days"
            }
    except sqlite3.Error as e:
        logger.error(f"Analytics query failed: {e}")
        return {"error": str(e)}

# Initialize database on import
init_db()