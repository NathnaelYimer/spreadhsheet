import asyncio
import websockets
import json
import base64
import numpy as np
import threading
import queue
import time
from typing import Callable, Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIRealtimeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket = None
        self.session_id = None
        self.is_connected = False
        self.is_recording = False
        self.is_playing = False
        self.is_processing = False  # Track if we're processing a response
        
        # Callbacks
        self.on_text_callback: Optional[Callable[[str, bool], None]] = None
        self.on_audio_callback: Optional[Callable[[bytes], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None
        self.on_session_created_callback: Optional[Callable[[], None]] = None
        self.on_speech_started_callback: Optional[Callable[[], None]] = None
        self.on_speech_stopped_callback: Optional[Callable[[], None]] = None
        
        # Audio queues
        self.audio_input_queue = queue.Queue()
        self.audio_output_queue = queue.Queue()
        
        # Control events
        self.interrupt_event = asyncio.Event()
        self.stop_event = asyncio.Event()
        
        # Session configuration
        self.current_voice = "alloy"
        self.current_instructions = ""
        self.current_npc_name = "HR"
        
        # Voice configurations for different NPCs
        self.npc_voices = {
            "HR": {
                "voice": "alloy",
                "instructions": """You are Sarah Chen, HR Director at Venture Builder AI. 
                Speak in a warm, professional tone. Keep responses conversational and helpful.
                Be empathetic and supportive in your interactions.""",
                "sample": "Welcome to Venture Builder AI! How can I help you today?"
            },
            "CEO": {
                "voice": "echo",
                "instructions": """You are Alex Rivera, CEO of Venture Builder AI. 
                Speak with authority, vision, and a touch of inspiration. 
                Be confident and forward-thinking in your responses.""",
                "sample": "I'm Alex Rivera, CEO. Let's build the future together!"
            },
            "Engineer": {
                "voice": "fable",
                "instructions": """You are Maya Patel, Lead Engineer at Venture Builder AI. 
                Speak with technical expertise and enthusiasm. Be precise and helpful with technical questions.
                Show passion for innovation and problem-solving.""",
                "sample": "Hi! I'm Maya, your technical lead. What can I help you build today?"
            }
        }
        
    async def connect(self):
        """Connect to OpenAI Realtime API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            logger.info(f"Attempting to connect to OpenAI Realtime API...")
            logger.info(f"API Key (first 10 chars): {self.api_key[:10]}...")
            logger.info(f"Headers: {headers}")
            
            # Retry logic for connection
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.websocket = await websockets.connect(
                        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
                        extra_headers=headers,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=5
                    )
                    self.is_connected = True
                    logger.info("Connected to OpenAI Realtime API")
                    # Start listening for messages
                    asyncio.create_task(self._listen_for_messages())
                    return True
                except Exception as e:
                    logger.error(f"Connection attempt {attempt+1} failed: {e}")
                    await asyncio.sleep(2)
            # If all retries fail
            self.is_connected = False
            if self.on_error_callback:
                self.on_error_callback("Connection failed after retries.")
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to Realtime API: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            self.is_connected = False
            if self.on_error_callback:
                self.on_error_callback(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the API"""
        self.stop_event.set()
        self.is_connected = False
        self.is_processing = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")
            self.websocket = None
            
        logger.info("Disconnected from OpenAI Realtime API")
    
    async def configure_session(self, voice: str, instructions: str, npc_name: str = "HR"):
        """Configure the session with voice and instructions"""
        if not self.is_connected:
            return False
            
        self.current_voice = voice
        self.current_instructions = instructions
        self.current_npc_name = npc_name
        
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": instructions,
                "voice": voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "tools": [],
                "tool_choice": "auto",
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(session_config))
                logger.info(f"Session configured with voice: {voice} for {npc_name}")
                return True
            else:
                logger.error("WebSocket not connected")
                return False
        except Exception as e:
            logger.error(f"Failed to configure session: {e}")
            return False
    
    async def send_audio_chunk(self, audio_data: bytes):
        """Send audio chunk to the API"""
        if not self.is_connected or not self.websocket:
            return
            
        # Convert audio data to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send audio chunk: {e}")
            if self.on_error_callback:
                self.on_error_callback(f"Failed to send audio chunk: {e}")
    
    async def commit_audio_buffer(self):
        """Commit the audio buffer to trigger response generation"""
        logger.debug("[COMMIT AUDIO BUFFER] Attempting to commit audio buffer...")
        if not self.is_connected or not self.websocket:
            logger.error("[COMMIT AUDIO BUFFER] Not connected or websocket missing. Commit aborted.")
            if self.on_error_callback:
                self.on_error_callback("[COMMIT AUDIO BUFFER] Not connected or websocket missing. Commit aborted.")
            return
        message = {
            "type": "input_audio_buffer.commit"
        }
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                self.is_processing = True
                logger.info("[COMMIT AUDIO BUFFER] Audio buffer committed, waiting for response...")
            else:
                logger.error("[COMMIT AUDIO BUFFER] WebSocket not connected")
                if self.on_error_callback:
                    self.on_error_callback("[COMMIT AUDIO BUFFER] WebSocket not connected")
        except Exception as e:
            logger.error(f"[COMMIT AUDIO BUFFER] Failed to commit audio buffer: {e}")
            if self.on_error_callback:
                self.on_error_callback(f"[COMMIT AUDIO BUFFER] Failed to commit audio buffer: {e}")
    
    async def send_text_message(self, text: str, npc_name: Optional[str] = None, preview_mode: bool = False):
        """Send a text message to the conversation"""
        if not self.is_connected or not self.websocket:
            return
            
        # If npc_name is provided, configure the session for that NPC
        if npc_name and npc_name in self.npc_voices:
            voice_config = self.npc_voices[npc_name]
            # npc_name is guaranteed to be a string at this point due to the check above
            await self.configure_session(voice_config["voice"], voice_config["instructions"], npc_name)
        
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                
                # Trigger response generation
                response_message = {
                    "type": "response.create",
                    "response": {
                        "modalities": ["text", "audio"],
                        "instructions": self.current_instructions
                    }
                }
                await self.websocket.send(json.dumps(response_message))
                self.is_processing = True
                
                if preview_mode:
                    logger.info(f"Preview mode: Sending text to {npc_name}")
                else:
                    logger.info("Text message sent, waiting for response...")
            else:
                logger.error("WebSocket not connected")
            
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
    
    async def interrupt_response(self):
        """Interrupt the current response"""
        if not self.is_connected or not self.websocket:
            return
            
        message = {
            "type": "response.cancel"
        }
        
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                self.interrupt_event.set()
                self.is_processing = False
                self.is_playing = False
                logger.info("Response interrupted by user")
            else:
                logger.error("WebSocket not connected")
        except Exception as e:
            logger.error(f"Failed to interrupt response: {e}")
    
    def get_npc_voice_config(self, npc_name: str):
        """Get voice configuration for a specific NPC"""
        return self.npc_voices.get(npc_name, self.npc_voices["HR"])
    
    def set_npc_voice_config(self, npc_name: str, voice: str, instructions: str, sample: str = ""):
        """Set voice configuration for a specific NPC"""
        self.npc_voices[npc_name] = {
            "voice": voice,
            "instructions": instructions,
            "sample": sample
        }
        logger.info(f"Updated voice config for {npc_name}: {voice}")
    
    async def _listen_for_messages(self):
        """Listen for messages from the API"""
        if not self.websocket:
            logger.error("WebSocket not available for listening")
            return
            
        try:
            async for message in self.websocket:
                if self.stop_event.is_set():
                    break
                    
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            self.is_connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming messages from the API"""
        message_type = data.get("type")
        logger.info(f"Received message type: {message_type}")
        print(f"DEBUG: Received message type: {message_type}")
        
        if message_type == "session.created":
            self.session_id = data.get("session", {}).get("id")
            logger.info(f"Session created: {self.session_id}")
            if self.on_session_created_callback:
                self.on_session_created_callback()
                
        elif message_type == "response.audio.delta":
            # Handle audio response chunks
            audio_data = data.get("delta")
            print(f"DEBUG: Received audio delta with {len(audio_data) if audio_data else 0} bytes")
            if audio_data and self.on_audio_callback:
                try:
                    audio_bytes = base64.b64decode(audio_data)
                    print(f"DEBUG: Decoded audio bytes: {len(audio_bytes)} bytes")
                    self.on_audio_callback(audio_bytes)
                    self.is_playing = True
                except Exception as e:
                    logger.error(f"Failed to decode audio data: {e}")
            else:
                print(f"DEBUG: No audio callback or no audio data")
                    
        elif message_type == "response.text.delta":
            # Handle text response chunks
            text_data = data.get("delta")
            logger.info(f"Received text delta: {text_data}")
            if text_data and self.on_text_callback:
                self.on_text_callback(text_data, False)  # False = partial
                
        elif message_type == "response.text.done":
            # Handle completed text response
            text_data = data.get("text")
            logger.info(f"Received text done: {text_data}")
            if text_data and self.on_text_callback:
                self.on_text_callback(text_data, True)  # True = complete
                
        elif message_type == "response.audio_transcript.delta":
            # Handle audio transcript (what the AI is saying)
            transcript = data.get("delta")
            logger.info(f"Received audio transcript delta: {transcript}")
            if transcript and self.on_text_callback:
                self.on_text_callback(transcript, False)
                
        elif message_type == "response.audio_transcript.done":
            # Handle completed audio transcript
            transcript = data.get("transcript")
            logger.info(f"Received audio transcript done: {transcript}")
            if transcript and self.on_text_callback:
                logger.info(f"Calling text callback with transcript: {transcript}")
                self.on_text_callback(transcript, True)
                logger.info(f"Audio transcript completed and sent to text callback: {transcript}")
            else:
                logger.warning(f"Audio transcript received but no callback or transcript: transcript={transcript}, callback={self.on_text_callback}")
                
        elif message_type == "input_audio_buffer.speech_started":
            logger.info("Speech started")
            self.is_recording = True
            if self.on_speech_started_callback:
                self.on_speech_started_callback()
            
        elif message_type == "input_audio_buffer.speech_stopped":
            logger.info("Speech stopped")
            self.is_recording = False
            if self.on_speech_stopped_callback:
                self.on_speech_stopped_callback()
            
        elif message_type == "response.done":
            logger.info("Response completed")
            self.is_playing = False
            self.is_processing = False
            
        elif message_type == "error":
            error_msg = data.get("error", {}).get("message", "Unknown error")
            # Suppress 'no active response found' as an error
            if "no active response found" in error_msg.lower():
                logger.info(f"API Cancellation Info: {error_msg}")
                # Do not call on_error_callback for this harmless case
                self.is_processing = False
                self.is_playing = False
            else:
                logger.error(f"API Error: {error_msg}")
                self.is_processing = False
                self.is_playing = False
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
        else:
            logger.debug(f"Unhandled message type: {message_type}")
            logger.debug(f"Message data: {data}")
    
    def set_callbacks(self, 
                     on_text: Optional[Callable[[str, bool], None]] = None,
                     on_audio: Optional[Callable[[bytes], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None,
                     on_session_created: Optional[Callable[[], None]] = None,
                     on_speech_started: Optional[Callable[[], None]] = None,
                     on_speech_stopped: Optional[Callable[[], None]] = None):
        """Set callback functions"""
        if on_text:
            self.on_text_callback = on_text
            logger.info("Text callback set successfully")
        if on_audio:
            self.on_audio_callback = on_audio
            logger.info("Audio callback set successfully")
        if on_error:
            self.on_error_callback = on_error
            logger.info("Error callback set successfully")
        if on_session_created:
            self.on_session_created_callback = on_session_created
            logger.info("Session created callback set successfully")
        if on_speech_started:
            self.on_speech_started_callback = on_speech_started
            logger.info("Speech started callback set successfully")
        if on_speech_stopped:
            self.on_speech_stopped_callback = on_speech_stopped
            logger.info("Speech stopped callback set successfully")
