import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_REALTIME_API_KEY = os.getenv('OPENAI_REALTIME_API_KEY', OPENAI_API_KEY)
    
    # Audio Configuration
    SAMPLE_RATE = 24000  # 24kHz for better quality
    CHANNELS = 1
    CHUNK_SIZE = 1024
    
    # Speech Detection
    VAD_THRESHOLD = 0.01
    SILENCE_DURATION = 0.5
    AUDIO_TIMEOUT = 1.0
    
    # Game Configuration
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    FPS = 60
    INTERACTION_DISTANCE = 2.0
    
    # Voice Configuration
    NPC_VOICES = {
        "HR": {
            "voice": "alloy",
            "instructions": """You are Sarah Chen, HR Director at Venture Builder AI. 
            Speak in a warm, professional tone. Keep responses conversational and helpful.
            Use natural speech patterns with occasional filler words like 'um' or 'well'.
            Maintain a supportive demeanor while being informative about company policies and culture.
            Keep responses concise but meaningful, typically 2-3 sentences."""
        },
        "CEO": {
            "voice": "echo", 
            "instructions": """You are Michael Chen, CEO of Venture Builder AI.
            Speak with confidence and vision. Use storytelling to illustrate points.
            Reference data and metrics when relevant. Balance optimism with realism.
            Maintain an approachable yet authoritative tone.
            Keep responses engaging but focused, typically 2-3 sentences."""
        }
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in your .env file.")
        
        if not cls.OPENAI_REALTIME_API_KEY:
            print("Warning: OPENAI_REALTIME_API_KEY not set. Using OPENAI_API_KEY as fallback.")
        
        return True
