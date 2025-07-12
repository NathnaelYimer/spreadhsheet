import sounddevice as sd
import numpy as np
import threading
import queue
import time
import asyncio
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self, sample_rate: int = 24000, channels: int = 1, chunk_size: int = 1024, input_device: Optional[int] = None, output_device: Optional[int] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.input_device = input_device
        self.output_device = output_device
        
        # Audio streams
        self.input_stream: Optional[sd.InputStream] = None
        self.output_stream: Optional[sd.OutputStream] = None
        
        # Queues for audio data
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Control flags
        self.is_recording = False
        self.is_playing = False
        self.should_stop = False
        
        # Callbacks
        self.on_audio_input: Optional[Callable[[bytes], None]] = None
        
        # Threading
        self.input_thread: Optional[threading.Thread] = None
        self.output_thread: Optional[threading.Thread] = None
        
        # Volume control
        self.input_volume = 1.0
        self.output_volume = 1.0
        
        # Voice Activity Detection
        self.vad_threshold = 0.01
        self.silence_duration = 0.5  # seconds
        self.last_speech_time = 0
        
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.is_recording:
            return
            
        try:
            print("Available audio devices:")
            print(sd.query_devices())
            print("Using input device:", self.input_device)
            self.is_recording = True
            self.should_stop = False
            
            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Audio input status: {status}")
                
                # Apply volume control
                audio_data = indata * self.input_volume
                
                # Convert to int16 PCM
                audio_int16 = (audio_data * 32767).astype(np.int16)
                
                # Voice Activity Detection
                rms = np.sqrt(np.mean(audio_int16.astype(np.float32) ** 2))
                print("Audio data shape:", indata.shape, "RMS:", rms)  # Debug print
                if rms > self.vad_threshold:
                    self.last_speech_time = time.time()
                
                # Put audio data in queue
                self.input_queue.put(audio_int16.tobytes())
                
                # Call callback if set
                if self.on_audio_input:
                    self.on_audio_input(audio_int16.tobytes())
            
            self.input_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=audio_callback,
                device=self.input_device
            )
            
            self.input_stream.start()
            logger.info("Audio recording started")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
            
        logger.info("Audio recording stopped")
    
    def start_playback(self):
        """Start audio playback"""
        if self.is_playing:
            return
        try:
            self.is_playing = True
            self.should_stop = False
            # Debug print for output device
            import sounddevice as sd
            try:
                if self.output_device is not None:
                    device_info = sd.query_devices(self.output_device)
                    print(f"[DEBUG] Using output device {self.output_device}: {device_info['name']}")  # type: ignore
                else:
                    print(f"[DEBUG] Using default output device (None specified)")
            except Exception as e:
                print(f"[DEBUG] Could not query output device info: {e}")
            def playback_worker():
                """Worker thread for audio playback"""
                buffer = np.array([], dtype=np.int16)
                
                def audio_callback(outdata, frames, time, status):
                    nonlocal buffer
                    
                    if status:
                        logger.warning(f"Audio output status: {status}")
                    
                    # Try to get audio data from queue
                    while not self.output_queue.empty() and len(buffer) < frames:
                        try:
                            audio_chunk = self.output_queue.get_nowait()
                            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
                            buffer = np.concatenate([buffer, audio_array])
                        except queue.Empty:
                            break
                    
                    # Fill output buffer
                    if len(buffer) >= frames:
                        # Take required frames from buffer
                        output_data = buffer[:frames].astype(np.float32) / 32767.0
                        buffer = buffer[frames:]
                        
                        # Apply volume control
                        output_data *= self.output_volume
                        
                        # Reshape for output
                        outdata[:] = output_data.reshape(-1, self.channels)
                        logger.debug(f"Playing audio chunk of {frames} frames")
                    else:
                        # Not enough data, output silence
                        outdata.fill(0)
                        logger.debug("Playing silence due to insufficient audio data")
                
                self.output_stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.float32,
                    blocksize=self.chunk_size,
                    callback=audio_callback,
                    device=self.output_device
                )
                
                self.output_stream.start()
                
                # Keep the stream alive
                while self.is_playing and not self.should_stop:
                    time.sleep(0.01)
                
                if self.output_stream:
                    self.output_stream.stop()
                    self.output_stream.close()
                    self.output_stream = None
            
            self.output_thread = threading.Thread(target=playback_worker, daemon=True)
            self.output_thread.start()
            
            logger.info("Audio playback started")
            
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            self.is_playing = False
    
    def stop_playback(self):
        """Stop audio playback"""
        if not self.is_playing:
            return
            
        self.is_playing = False
        self.should_stop = True
        
        if self.output_thread:
            self.output_thread.join(timeout=1.0)
            self.output_thread = None
            
        logger.info("Audio playback stopped")
    
    def play_audio_chunk(self, audio_data: bytes):
        """Add audio chunk to playback queue and start playback if not running"""
        if not self.is_playing:
            self.start_playback()
        self.output_queue.put(audio_data)
    
    def get_audio_chunk(self) -> Optional[bytes]:
        """Get audio chunk from input queue"""
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            return None
    
    def clear_queues(self):
        """Clear all audio queues"""
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                break
                
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
    
    def set_volumes(self, input_volume: Optional[float] = None, output_volume: Optional[float] = None):
        """Set input and output volumes (0.0 to 1.0)"""
        if input_volume is not None:
            self.input_volume = max(0.0, min(1.0, input_volume))
        if output_volume is not None:
            self.output_volume = max(0.0, min(1.0, output_volume))
    
    def is_speech_detected(self) -> bool:
        """Check if speech was detected recently"""
        return (time.time() - self.last_speech_time) < self.silence_duration
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.stop_playback()
        self.clear_queues()
