"""Configuration settings for TalentScout Hiring Assistant."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # OpenAI Configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1")
    
    # Application Configuration
    APP_TITLE = "TalentScout Hiring Assistant"
    APP_DESCRIPTION = "Intelligent chatbot for initial candidate screening"
    
    # Data Storage
    CANDIDATES_FILE = "data/candidates.json"
    
    # Conversation Settings
    MAX_QUESTIONS_PER_TECH = 3
    CONVERSATION_TIMEOUT = 1800  # 30 minutes
    
    # UI Settings
    CHAT_HEIGHT = 400
    SIDEBAR_WIDTH = 300
    
    # Privacy Settings
    ENCRYPT_DATA = True
    RETAIN_DATA_DAYS = 30

# Create global settings instance
settings = Settings()