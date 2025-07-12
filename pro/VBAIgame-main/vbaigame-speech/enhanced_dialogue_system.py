import pygame
import asyncio
import threading
import time
import queue
from typing import Optional, Dict, Any
import logging
from realtime_client import OpenAIRealtimeClient
from audio_manager import AudioManager
from settings_overlay import SettingsOverlay
# Add explicit OpenGL imports
from OpenGL.GL import (
    glPushAttrib, GL_ALL_ATTRIB_BITS, glMatrixMode, GL_PROJECTION, glPushMatrix, glLoadIdentity,
    glOrtho, GL_MODELVIEW, glDisable, GL_DEPTH_TEST, glEnable, GL_BLEND, glBlendFunc,
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TEXTURE_2D, glBindTexture, glTexParameteri,
    GL_TEXTURE_MIN_FILTER, GL_LINEAR, GL_TEXTURE_MAG_FILTER, glTexImage2D, GL_RGBA,
    GL_UNSIGNED_BYTE, glBegin, GL_QUADS, glTexCoord2f, glVertex2f, glEnd, glPopMatrix, glPopAttrib,
    glGenTextures
)

logger = logging.getLogger(__name__)

class EnhancedDialogueSystem:
    def __init__(self, openai_api_key: str):
        # Ensure async_thread and async_loop are always defined first
        self.async_thread = None
        self.async_loop = None
        # Initialize existing components
        self.active = False
        self.user_input = ""
        self.npc_message = ""
        self.input_active = False
        self.current_npc = None
        self.initial_player_pos = None
        
        # Font setup
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 24)
            logger.info("Font loaded successfully")
        except Exception as e:
            logger.error(f"Font loading failed: {e}")
        
        # UI components
        self.ui_surface = pygame.Surface((800, 600), pygame.SRCALPHA).convert_alpha()
        self.ui_texture = glGenTextures(1)
        
        # Speech-to-speech components
        from audio_utils import get_first_microphone_device, list_input_devices
        self.realtime_client = OpenAIRealtimeClient(openai_api_key)
        # Automatically detect the first available microphone
        detected_device = get_first_microphone_device()
        if detected_device is None:
            detected_device = 0
        self.input_devices = list_input_devices()
        self.selected_input_device = detected_device
        self.audio_manager = AudioManager(sample_rate=24000, input_device=detected_device, output_device=4)
        
        # Set up audio callback
        self.audio_manager.on_audio_input = self._on_audio_input
        
        # Audio processing
        self.audio_buffer = queue.Queue()
        self.last_audio_time = 0
        self.audio_timeout = 1.0  # seconds
        self.audio_gain = 5.0  # Amplify audio by this factor (1.0 = no gain)
        
        # Setup callbacks (only once, here)
        self._setup_callbacks()
        
        # Speech control
        self.speech_mode = False
        self.is_listening = False
        self.is_speaking = False
        self.speech_enabled = True

        # NPC voice configurations
        self.npc_voices = {
            "HR": {
                "voice": "alloy",
                "instructions": """You are Sarah Chen, HR Director at Venture Builder AI. Speak in a warm, professional tone. Keep responses conversational and helpful.""",
                "sample": "Welcome to Venture Builder AI! How can I help you today?"
            },
            "CEO": {
                "voice": "echo",
                "instructions": """You are Alex Rivera, CEO of Venture Builder AI. Speak with authority, vision, and a touch of inspiration.""",
                "sample": "I'm Alex Rivera, CEO. Let's build the future together!"
            }
        }
        
        # Settings overlay
        self.settings_overlay = SettingsOverlay(font=self.font)
        self.settings_overlay.set_npc_voices(self.npc_voices)
        self.settings_overlay.set_voice_preview_callback(self._preview_voice)
        # Pass input device list to settings overlay
        self.settings_overlay.set_input_devices(self.input_devices, self.selected_input_device)
        self.settings_overlay.set_input_device_callback(self._on_input_device_selected)
        self.settings_icon_rect = pygame.Rect(740, 0, 40, 40)  # Position to match UI
        self.settings_open = False

        # Debug: print selected microphone device info
        import sounddevice as sd
        try:
            device_info = sd.query_devices(self.audio_manager.input_device)
            print(f"[DEBUG] Using input device {self.audio_manager.input_device}: {device_info['name']}")  # type: ignore
            print(f"[DEBUG] Device info: {device_info}")
            print(f"[DEBUG] All available input devices: {self.input_devices}")
        except Exception as e:
            print(f"[DEBUG] Could not query device info: {e}")

    def _on_input_device_selected(self, device_idx):
        """Callback when user selects a new input device from settings overlay."""
        import sounddevice as sd
        from audio_manager import AudioManager
        self.selected_input_device = device_idx
        # Re-initialize AudioManager with new device, keep output device same
        try:
            self.audio_manager = AudioManager(sample_rate=24000, input_device=device_idx, output_device=self.audio_manager.output_device)
            self.audio_manager.on_audio_input = self._on_audio_input
            device_info = sd.query_devices(device_idx)
            print(f"[DEBUG] Switched to input device {device_idx}: {device_info['name']}")  # type: ignore
        except Exception as e:
            print(f"[DEBUG] Could not switch to device {device_idx}: {e}")
        # Update overlay to highlight new selection
        if hasattr(self, 'settings_overlay'):
            self.settings_overlay.set_input_devices(self.input_devices, device_idx)

    def _preview_voice(self, npc_name):
        """Play a sample phrase using the selected NPC's voice via realtime_client."""
        if npc_name not in self.npc_voices:
            return
        voice_cfg = self.npc_voices[npc_name]
        sample_text = voice_cfg.get('sample', 'Hello, this is my voice!')
        # Use realtime_client to synthesize and play
        if hasattr(self, 'realtime_client') and self.realtime_client.is_connected and self.async_loop is not None:
            async def preview_voice_sample():
                await self.realtime_client.send_text_message(sample_text, npc_name=npc_name, preview_mode=True)
            asyncio.run_coroutine_threadsafe(preview_voice_sample(), self.async_loop)
        else:
            self.settings_overlay.message = "Realtime API not connected."
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup callbacks for realtime client"""
        self.realtime_client.set_callbacks(
            on_text=self._on_text_received,
            on_audio=self._on_audio_received,
            on_error=self._on_error,
            on_session_created=self._on_session_created,
            on_speech_started=self._on_speech_started,
            on_speech_stopped=self._on_speech_stopped
        )
        print("DEBUG: Text callback set to", self._on_text_received)
    
    def _on_text_received(self, text: str, is_complete: bool):
        """Handle text responses from the API"""
        logger.info(f"Text received: '{text}' (complete: {is_complete})")
        if is_complete:
            self.npc_message = text
            logger.info(f"Complete NPC response: {text}")
        else:
            # For partial responses, append to current message
            if not hasattr(self, '_partial_response'):
                self._partial_response = ""
            self._partial_response += text
            self.npc_message = self._partial_response
    
    def _on_audio_received(self, audio_data: bytes):
        """Handle audio responses from the API"""
        try:
            print(f"INFO:enhanced_dialogue_system:Received audio response of {len(audio_data)} bytes")
            # Play the audio response
            if audio_data:
                logger.debug(f"Audio data type: {type(audio_data)}, length: {len(audio_data)}")
                logger.debug(f"[AUDIO RECEIVED] Playing audio response of {len(audio_data)} bytes")
                self.audio_manager.play_audio_chunk(audio_data)
                self.is_speaking = True
                logger.info(f"Playing audio response of {len(audio_data)} bytes")
                print(f"INFO:enhanced_dialogue_system:Audio sent to audio manager for playback")
            else:
                logger.warning("[AUDIO RECEIVED] No audio data to play")
        except Exception as e:
            logger.error(f"[AUDIO RECEIVED] Exception: {e}")
    
    def _on_error(self, error_message: str):
        """Handle errors from the API"""
        logger.error(f"Realtime API error: {error_message}")
        self.last_error_message = error_message
        
        # If it's a buffer too small error, try to recover
        if "buffer too small" in error_message.lower():
            logger.info("Attempting to recover from buffer error...")
            # Don't disable speech mode for this error, just log it
        elif "cancellation failed" in error_message.lower():
            logger.info("Cancellation failed error received, ignoring to avoid disabling speech mode.")
            # Do not disable speech mode for cancellation failed errors
        else:
            # For other errors, disable speech mode
            self.speech_mode = False
            self.speech_enabled = False
            logger.info("Speech mode disabled due to error, fallback to text mode")
    
    def _on_session_created(self):
        """Handle session creation"""
        logger.info("Realtime session created successfully")
        self.last_error_message = ""  # Clear any previous errors
    
    def _on_speech_started(self):
        """Handle when the API detects speech started"""
        logger.info("API detected speech started")
        self.is_listening = True
    
    def _on_speech_stopped(self):
        """Handle when the API detects speech stopped"""
        logger.info("API detected speech stopped")
        self.is_listening = False
    
    def _on_audio_input(self, audio_data):
        import numpy as np
        # Convert bytes to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        audio_np = audio_np.reshape(-1)  # Force 1D
        logger.debug(f"[AUDIO INPUT] Chunk shape after reshape: {audio_np.shape}")
        # Amplify audio
        audio_np *= self.audio_gain
        # Calculate RMS
        rms = np.sqrt(np.mean(np.square(audio_np)))
        logger.debug(f"[AUDIO INPUT] Audio data shape: {audio_np.shape} RMS: {rms:.6f}")
        if rms < 0.0001:
            logger.info(f"[AUDIO INPUT] Audio chunk discarded due to low RMS ({rms:.6f})")
            print(f"INFO:enhanced_dialogue_system:Audio chunk discarded due to low RMS ({rms:.6f})")
            return
        self.audio_buffer.put(audio_np)  # Always 1D, use put for queue
        logger.info(f"Audio chunk accepted with RMS {rms:.6f}")

    def start_conversation(self, npc_role: str = "HR", player_pos=None):
        """Start conversation with NPC"""
        self.active = True
        self.input_active = True
        self.current_npc = npc_role
        self.initial_player_pos = [player_pos[0], player_pos[1], player_pos[2]] if player_pos else [0, 0.5, 0]
        
        # Start async loop for realtime operations
        self._start_async_loop()
        
        # Configure voice for this NPC
        voice_config = self.npc_voices.get(npc_role, self.npc_voices["HR"])
        
        # Set initial greeting
        initial_messages = {
            "HR": "Hello! I'm Sarah, the HR Director. You can talk to me or type - whatever's more comfortable!",
            "CEO": "Hi there! I'm Michael, the CEO. Feel free to speak with me or use the text box below."
        }
        
        self.npc_message = initial_messages.get(npc_role, "Hello! How can I help you today?")
        
        # Setup realtime session asynchronously
        if self.speech_enabled and self.async_loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._setup_realtime_session(voice_config),
                self.async_loop
            )
        
        logger.info(f"Conversation started with {npc_role}")
    
    def _start_async_loop(self):
        """Start the async event loop in a separate thread"""
        if self.async_thread and self.async_thread.is_alive():
            return
            
        def run_async_loop():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            self.async_loop.run_forever()
        
        self.async_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Wait for loop to be ready
        while self.async_loop is None:
            time.sleep(0.01)
    
    async def _setup_realtime_session(self, voice_config: Dict[str, str]):
        """Setup the realtime session with voice configuration"""
        try:
            # Connect to realtime API
            if await self.realtime_client.connect():
                # Configure session with current NPC
                npc_role = self.current_npc or "HR"
                await self.realtime_client.configure_session(
                    voice=voice_config["voice"],
                    instructions=voice_config["instructions"],
                    npc_name=npc_role
                )
                logger.info(f"Realtime session configured successfully for {npc_role}")
            else:
                logger.error("Failed to connect to realtime API")
        except Exception as e:
            logger.error(f"Error setting up realtime session: {e}")
    
    def toggle_speech_mode(self):
        """Toggle between speech and text mode with extra diagnostics"""
        if not self.speech_enabled:
            logger.warning("Speech mode toggle attempted but speech is disabled.")
            self.last_error_message = "Speech mode is disabled."
            return
        self.speech_mode = not self.speech_mode
        logger.info(f"Speech mode toggled to: {'ON' if self.speech_mode else 'OFF'}")
        if self.speech_mode:
            logger.info("Starting speech mode...")
            self._start_speech_mode()
        else:
            self._stop_speech_mode()
    
    def _start_speech_mode(self):
        try:
            logger.info("Attempting to start speech mode: starting audio recording and playback...")
            
            # Check if realtime client is connected
            if not self.realtime_client.is_connected:
                logger.warning("Realtime client not connected. Attempting to reconnect...")
                # Try to reconnect
                if self.async_loop is not None:
                    npc_role = self.current_npc or "HR"
                    voice_config = self.npc_voices.get(npc_role, self.npc_voices["HR"])
                    asyncio.run_coroutine_threadsafe(
                        self._setup_realtime_session(voice_config),
                        self.async_loop
                    )
                    # Wait a bit for connection
                    time.sleep(1.0)
                
                if not self.realtime_client.is_connected:
                    logger.error("Failed to connect to realtime API")
                    self.last_error_message = "Voice API connection failed. Please try again."
                    self.speech_mode = False
                    return
            
            # Ensure audio_manager has correct output device from settings overlay if available
            if hasattr(self.settings_overlay, 'output_volume'):
                self.audio_manager.set_volumes(output_volume=self.settings_overlay.output_volume)
            
            self.audio_manager.start_recording()
            self.audio_manager.start_playback()
            self.is_listening = True
            logger.info("Microphone and speaker streams started. Listening for user speech.")
            threading.Thread(target=self._process_audio_input, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start speech mode: {e}")
            self.last_error_message = f"Failed to start speech mode: {e}"
            self.speech_mode = False
    
    def _stop_speech_mode(self):
        """Stop speech mode"""
        self.is_listening = False
        self.audio_manager.stop_recording()
        self.audio_manager.stop_playback()
        self.audio_manager.clear_queues()
    
    def _process_audio_input(self):
        import numpy as np
        import time
        accumulated_audio = []
        accumulated_duration = 0.0
        sample_rate = self.audio_manager.sample_rate
        chunk_size = 1024  # Should match AudioManager
        chunk_duration = chunk_size / sample_rate
        min_commit_duration = 0.5  # 500ms - increased to ensure enough audio
        while self.speech_mode:
            try:
                audio_data = self.audio_buffer.get(timeout=0.1)
                accumulated_audio.append(audio_data)
                accumulated_duration += chunk_duration
                logger.debug(f"[AUDIO BUFFER] Accumulated duration: {accumulated_duration:.3f}s")
                if accumulated_duration >= min_commit_duration:
                    audio_to_send = np.concatenate(accumulated_audio).reshape(-1)  # Ensure 1D
                    logger.debug(f"[AUDIO BUFFER] Preparing to send buffer of shape {audio_to_send.shape}, dtype={audio_to_send.dtype}, duration={audio_to_send.shape[0]/sample_rate:.3f}s")
                    print(f"DEBUG: Sending audio buffer of {audio_to_send.shape}, dtype={audio_to_send.dtype}, duration={audio_to_send.shape[0]/sample_rate:.3f}s")
                    if audio_to_send.size == 0:
                        logger.info("[AUDIO BUFFER] Audio buffer empty, skipping commit")
                        print("INFO:enhanced_dialogue_system:Audio buffer empty, skipping commit")
                        accumulated_audio = []
                        accumulated_duration = 0.0
                        continue
                    # Convert to PCM16, clip to valid range
                    audio_int16 = np.clip(audio_to_send, -32768, 32767).astype(np.int16)
                    logger.debug(f"[AUDIO BUFFER] Converted to int16: {audio_int16.shape}, dtype={audio_int16.dtype}")
                    print(f"DEBUG: Final audio buffer sent: {audio_int16.shape}, dtype={audio_int16.dtype}")
                    try:
                        if self.realtime_client.is_connected and self.async_loop is not None:
                            import asyncio
                            asyncio.run_coroutine_threadsafe(
                                self.realtime_client.send_audio_chunk(audio_int16.tobytes()),
                                self.async_loop
                            )
                            asyncio.run_coroutine_threadsafe(
                                self.realtime_client.commit_audio_buffer(),
                                self.async_loop
                            )
                    except Exception as e:
                        logger.error(f"[AUDIO BUFFER] Exception during commit: {e}")
                        print(f"ERROR:enhanced_dialogue_system:Exception during audio buffer commit: {e}")
                    accumulated_audio = []
                    accumulated_duration = 0.0
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[AUDIO BUFFER] Exception in audio processing: {e}")
                print(f"INFO:enhanced_dialogue_system:Exception in audio processing: {e}")
                continue
        logger.info("[AUDIO BUFFER] Audio processing thread stopped")
        print("INFO:enhanced_dialogue_system:Audio processing thread stopped")
    
    def send_text_message(self):
        """Send text message (existing functionality enhanced)"""
        if not self.user_input.strip():
            return

        # Interrupt any ongoing speech before sending new text
        self.interrupt_speech()

        user_message = self.user_input.strip()
        logger.info(f"User text message: {user_message}")
        npc_name = self.current_npc or "HR"
        # Check connection status
        logger.info(f"Realtime client connected: {self.realtime_client.is_connected}")
        logger.info(f"Async loop available: {self.async_loop is not None}")
        # Send to realtime API if connected
        if self.realtime_client.is_connected and self.async_loop is not None:
            logger.info("Configuring session for text-to-speech...")
            import asyncio
            # Always configure session for audio before sending text
            voice_config = self.npc_voices.get(npc_name, self.npc_voices["HR"])
            asyncio.run_coroutine_threadsafe(
                self.realtime_client.configure_session(
                    voice_config["voice"],
                    voice_config["instructions"],
                    npc_name
                ),
                self.async_loop
            )
            logger.info("Sending message to realtime API...")
            asyncio.run_coroutine_threadsafe(
                self.realtime_client.send_text_message(user_message, npc_name=npc_name),
                self.async_loop
            )
        else:
            # Fallback to original text-based system
            logger.warning("Realtime API not connected, using fallback response")
            self._fallback_text_response(user_message)
        self.user_input = ""
    
    def _fallback_text_response(self, user_message: str):
        """Fallback to original text-based response system"""
        # Provide a more intelligent fallback response based on the NPC
        npc_role = self.current_npc or "HR"
        
        if npc_role == "HR":
            self.npc_message = f"Hi! I'm Sarah from HR. You said: '{user_message}'. I'd be happy to help you with any questions about our company policies, benefits, or workplace culture. What would you like to know?"
        elif npc_role == "CEO":
            self.npc_message = f"Hello! I'm Michael, the CEO. You mentioned: '{user_message}'. I'm here to discuss our company's vision, strategy, or any other business matters. How can I assist you today?"
        else:
            self.npc_message = f"Thanks for your message: '{user_message}'. I'm here to help! What would you like to discuss?"
        
        logger.warning(f"Using fallback response - realtime API may not be connected properly")
    
    def interrupt_speech(self):
        """Interrupt current speech"""
        # Always stop playback and clear queues
        self.audio_manager.stop_playback()
        self.audio_manager.clear_queues()
        self.is_speaking = False
        if hasattr(self.realtime_client, 'is_playing'):
            self.realtime_client.is_playing = False

        # If the realtime client is connected and async loop is available, send cancel
        if self.realtime_client.is_connected and self.async_loop is not None:
            import asyncio
            asyncio.run_coroutine_threadsafe(
                self.realtime_client.interrupt_response(),
                self.async_loop
            )
            logger.info("Speech interrupted by player (forced)")
        else:
            logger.info("Speech interrupted locally (no active API connection)")
    
    def handle_input(self, event):
        """Handle input events (enhanced, with settings overlay)"""
        if self.settings_overlay.active:
            self.settings_overlay.handle_event(event)
            # Sync overlay controls to audio manager
            self.audio_manager.set_volumes(
                input_volume=self.settings_overlay.input_volume,
                output_volume=self.settings_overlay.output_volume
            )
            return
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            # ESC opens/closes settings overlay
            if event.key == pygame.K_ESCAPE:
                if not self.settings_overlay.active:
                    self.settings_overlay.open()
                else:
                    self.settings_overlay.close()
                return
            # Check for Shift+Q to exit
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] and event.key == pygame.K_q:
                self._cleanup()
                self.active = False
                self.input_active = False
                return {"command": "move_player_back", "position": self.initial_player_pos}
            # Toggle speech mode with 'V' key
            elif event.key == pygame.K_v:
                self.toggle_speech_mode()
            # Interrupt speech with spacebar
            elif event.key == pygame.K_SPACE and self.is_speaking:
                self.interrupt_speech()
            # Handle text input
            elif self.input_active:
                if event.key == pygame.K_RETURN and self.user_input.strip():
                    self.send_text_message()
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                elif event.unicode.isprintable():
                    self.user_input += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Click on settings icon
            mouse_x, mouse_y = event.pos
            if self.settings_icon_rect.collidepoint(mouse_x, mouse_y):
                self.settings_overlay.open()
                return
    
    def render(self):
        """Render the dialogue interface (enhanced)"""
        if not self.active:
            return
            
        self.ui_surface.fill((0, 0, 0, 0))
        
        box_height = 280  # Increased height for speech controls and error display
        box_y = 600 - box_height - 20
        
        # Enhanced Background with shadow for readability
        shadow_color = (30, 30, 30, 180)
        pygame.draw.rect(self.ui_surface, shadow_color, (16, box_y+4, 800 - 32, box_height+8), border_radius=18)
        box_color = (25, 25, 25, 235)
        pygame.draw.rect(self.ui_surface, box_color, (20, box_y, 800 - 40, box_height), border_radius=16)
        pygame.draw.rect(self.ui_surface, (255, 255, 255, 240), (20, box_y, 800 - 40, box_height), 2, border_radius=16)

        y_offset = box_y + 16

        # Mode icons and indicators
        icon_font = pygame.font.Font(None, 36)
        mode_icon = "🎤" if self.speech_mode else "⌨️"
        mode_label = "Speech Mode" if self.speech_mode else "Text Mode"
        mode_color = (0, 220, 0) if self.speech_mode else (90, 180, 255)
        pygame.draw.circle(self.ui_surface, mode_color, (60, y_offset+20), 18)
        icon_surface = icon_font.render(mode_icon, True, (255,255,255))
        self.ui_surface.blit(icon_surface, (50, y_offset+8))
        label_surface = self.font.render(mode_label, True, mode_color)
        self.ui_surface.blit(label_surface, (85, y_offset+12))
        # Tooltip for settings (clickable area)
        settings_surface = self.font.render("⚙️", True, (220,220,220))
        self.ui_surface.blit(settings_surface, (740, y_offset+12))
        self.settings_icon_rect = pygame.Rect(740, y_offset+12, 36, 36)
        y_offset += 40

        # Exit instruction
        quit_text = self.font.render("Press Shift+Q to exit", True, (220, 220, 220))
        self.ui_surface.blit(quit_text, (40, y_offset))
        y_offset += 28

        # Speech/text state feedback
        if self.speech_enabled:
            if self.speech_mode:
                # Animated/colored feedback for listening/speaking/thinking
                if self.is_listening:
                    listen_color = (0, 255, 120)
                    listen_surface = self.font.render("🎤 Listening... (Press SPACE to interrupt)", True, listen_color)
                    self.ui_surface.blit(listen_surface, (40, y_offset))
                elif self.is_speaking:
                    speak_color = (255, 220, 0)
                    speak_surface = self.font.render("🔊 Speaking... (Press SPACE to interrupt)", True, speak_color)
                    self.ui_surface.blit(speak_surface, (40, y_offset))
                else:
                    think_color = (120, 120, 255)
                    think_surface = self.font.render("💭 Thinking...", True, think_color)
                    self.ui_surface.blit(think_surface, (40, y_offset))
                y_offset += 28
            else:
                text_mode_surface = self.font.render("⌨️ Type your message and press Enter", True, (120, 220, 255))
                self.ui_surface.blit(text_mode_surface, (40, y_offset))
                y_offset += 28

        # Error message display (popup style)
        if hasattr(self, 'last_error_message') and self.last_error_message:
            err_bg = pygame.Surface((720, 36), pygame.SRCALPHA)
            err_bg.fill((255, 30, 30, 180))
            self.ui_surface.blit(err_bg, (40, y_offset))
            error_text = self.font.render(f"Error: {self.last_error_message}", True, (255, 255, 255))
            self.ui_surface.blit(error_text, (50, y_offset+4))
            y_offset += 40
            # Auto-clear error after a few seconds
            if not hasattr(self, '_last_error_time'):
                self._last_error_time = time.time()
            elif self._last_error_time is not None and time.time() - self._last_error_time > 4:
                self.last_error_message = ""
                self._last_error_time = None

        # NPC message
        if self.npc_message:
            self.render_text(self.ui_surface, self.npc_message, 40, y_offset)
            y_offset += self._get_text_height(self.npc_message) + 10

        # Text input
        if self.input_active:
            input_prompt = "> " + self.user_input + "_"
            input_surface = self.font.render(input_prompt, True, (255, 255, 255))
            self.ui_surface.blit(input_surface, (40, box_y + box_height - 48))

        # Settings overlay (on top)
        if self.settings_overlay.active:
            self.settings_overlay.render(self.ui_surface)
        # Render to OpenGL
        self._render_to_opengl()

    
    def render_text(self, surface, text, x, y):
        """Render wrapped text (existing method)"""
        max_width = 800 - 80
        line_height = 25
        
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = self.font.render(word + ' ', True, (255, 255, 255))
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            surface.blit(text_surface, (x, y + i * line_height))
        
        return len(lines) * line_height
    
    def _get_text_height(self, text):
        """Get the height of rendered text"""
        max_width = 800 - 80
        words = text.split()
        lines = 1
        current_width = 0
        
        for word in words:
            word_surface = self.font.render(word + ' ', True, (255, 255, 255))
            word_width = word_surface.get_width()
            
            if current_width + word_width > max_width:
                lines += 1
                current_width = word_width
            else:
                current_width += word_width
        
        return lines * 25
    
    def _render_to_opengl(self):
        """Render UI surface to OpenGL (existing method)"""
        texture_data = pygame.image.tostring(self.ui_surface, "RGBA", True)
        
        # Save OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 800, 0, 600, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Setup 2D rendering
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        
        # Update texture
        glBindTexture(GL_TEXTURE_2D, self.ui_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 800, 600, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Draw texture
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(800, 0)
        glTexCoord2f(1, 1); glVertex2f(800, 600)
        glTexCoord2f(0, 1); glVertex2f(0, 600)
        glEnd()
        
        # Restore OpenGL state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()
    
    def _cleanup(self):
        """Clean up resources"""
        self._stop_speech_mode()
        
        # Stop speech mode and clear audio
        self.speech_mode = False
        self.is_listening = False
        self.is_speaking = False
        
        # Clean up audio manager
        self.audio_manager.cleanup()
        
        # Clean up realtime client properly
        if self.async_loop is not None and not self.async_loop.is_closed():
            try:
                # Cancel all pending tasks
                pending_tasks = asyncio.all_tasks(self.async_loop)
                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                
                # Disconnect realtime client
                if self.realtime_client and self.realtime_client.is_connected:
                    asyncio.run_coroutine_threadsafe(
                        self.realtime_client.disconnect(),
                        self.async_loop
                    )
                
                # Stop the event loop
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        # Wait for async thread to finish
        if self.async_thread and self.async_thread.is_alive():
            self.async_thread.join(timeout=2.0)
