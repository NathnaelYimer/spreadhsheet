# Speech-to-Speech Integration for VBAIgame

## Overview

This document describes the complete speech-to-speech integration using OpenAI's Realtime API in the VBAIgame project. The implementation enables real-time, natural voice interactions between players and NPCs while maintaining compatibility with text-based interactions.

## Features

### ✅ Implemented Features

1. **Real-time Speech-to-Speech Communication**
   - Players can speak to NPCs using their microphone
   - NPCs respond with natural, synthesized voices
   - Low-latency communication via WebSocket connections

2. **Dynamic Voice Configuration**
   - Multiple NPCs with unique voice personalities
   - Configurable voices: alloy, echo, fable
   - Context-aware instructions for each NPC

3. **Seamless Text Integration**
   - Text box remains fully functional
   - Players can switch between voice and text input
   - NPCs respond in both text and voice for all interactions

4. **Interruption Handling**
   - Players can interrupt NPC responses mid-sentence
   - Smooth transition between speaking and listening
   - Proper cleanup of interrupted audio streams

5. **Error Recovery**
   - Graceful handling of API errors
   - Automatic fallback to text mode on critical errors
   - Buffer management for optimal audio streaming

6. **Settings Overlay**
   - Volume controls for input and output
   - Voice preview functionality
   - Real-time configuration changes

## Controls & Usage

### How to Use
- **Start a Conversation:** Approach an NPC and press the interaction key.
- **Speak to NPC:** Press `V` (or the designated key) to activate the microphone. Speak your message, then release or wait for auto-stop.
- **Type to NPC:** Click the text box, type your message, and press `Enter`.
- **NPC Response:** NPCs reply in both text (dialogue box) and voice (audio output).

### Interruptions
- **Interrupt NPC Speech:** Press `Space` at any time to immediately stop the NPC’s voice response and prompt for new input.

### Settings Overlay
- **Open Settings:** Press `ESC` or click the ⚙️ icon.
- **Adjust Input/Output Volume:** Use the sliders in the overlay.
- **Change Devices:** Select from available input/output devices in the overlay.
- **Preview Voices:** Click the preview button next to each NPC to hear their configured voice.

### Status Indicators
- **Listening:** On-screen prompt or icon shows when the system is recording your voice.
- **Speaking:** Animation or icon shows when the NPC is speaking.
- **Typing:** Text box is active and waiting for your input.

### Troubleshooting
- Ensure your microphone and speakers are connected and selected in settings.
- If you encounter “no audio” or “device not found” errors, check your device selection and system permissions.
- For persistent issues, consult the debug output in the terminal.

## Architecture

### Core Components

1. **EnhancedDialogueSystem** (`enhanced_dialogue_system.py`)
   - Main interface for speech and text interactions
   - Manages audio processing and API communication
   - Handles UI rendering and user input

2. **OpenAIRealtimeClient** (`realtime_client.py`)
   - WebSocket connection to OpenAI Realtime API
   - Audio streaming and buffer management
   - Dynamic voice configuration for NPCs

3. **AudioManager** (`audio_manager.py`)
   - Microphone input and speaker output
   - Audio format conversion and processing
   - Volume control and voice activity detection

4. **SettingsOverlay** (`settings_overlay.py`)
   - User interface for audio settings
   - Voice preview and configuration
   - Real-time volume adjustment

### Data Flow

```
Player Speech → Microphone → AudioManager → OpenAIRealtimeClient → API
                                                                    ↓
Player Text → EnhancedDialogueSystem → OpenAIRealtimeClient → API
                                                                    ↓
API Response → OpenAIRealtimeClient → AudioManager → Speakers
                                    ↓
Text Response → EnhancedDialogueSystem → UI Display
```

## NPC Voice Configurations

### HR Director (Sarah Chen)
- **Voice**: alloy
- **Personality**: Warm, professional, supportive
- **Instructions**: "You are Sarah Chen, HR Director at Venture Builder AI. Speak in a warm, professional tone. Keep responses conversational and helpful. Be empathetic and supportive in your interactions."

### CEO (Alex Rivera)
- **Voice**: echo
- **Personality**: Confident, visionary, inspiring
- **Instructions**: "You are Alex Rivera, CEO of Venture Builder AI. Speak with authority, vision, and a touch of inspiration. Be confident and forward-thinking in your responses."

### Lead Engineer (Maya Patel)
- **Voice**: fable
- **Personality**: Technical, enthusiastic, precise
- **Instructions**: "You are Maya Patel, Lead Engineer at Venture Builder AI. Speak with technical expertise and enthusiasm. Be precise and helpful with technical questions. Show passion for innovation and problem-solving."

## Usage Instructions

### Starting the Game

1. Ensure your `.env` file contains a valid OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Run the enhanced game:
   ```bash
   python app_enhanced.py
   ```

## Technical Implementation

### Audio Processing

The system uses a sophisticated audio processing pipeline:

1. **Input Processing**
   - 16kHz mono PCM audio from microphone
   - Real-time RMS calculation for voice activity detection
   - Configurable volume control

2. **API Communication**
   - WebSocket connection to OpenAI Realtime API
   - Base64 encoding of audio chunks
   - Buffer accumulation for optimal API performance

3. **Output Processing**
   - Real-time audio playback
   - Volume control and format conversion
   - Interruption handling

### Buffer Management

To handle the "buffer too small" error from the OpenAI API:

1. **Audio Accumulation**: Collect at least 120ms of audio before committing
2. **Smart Committing**: Only commit when sufficient audio is available
3. **Error Recovery**: Graceful handling of buffer errors without disabling speech

### Interruption Handling

1. **User Interruption**: Space key cancels current response
2. **Audio Interruption**: Stops playback and clears audio queues
3. **API Interruption**: Sends cancel message to API
4. **State Management**: Proper cleanup of processing flags

## Troubleshooting

### Common Issues

1. **"Buffer too small" Error**
   - **Cause**: Insufficient audio data sent to API
   - **Solution**: System automatically adjusts buffer accumulation
   - **Prevention**: Speak clearly and ensure good microphone quality

2. **No Audio Input**
   - **Check**: Microphone permissions and device selection
   - **Verify**: Audio device list in console output
   - **Test**: Use text mode as fallback

3. **API Connection Issues**
   - **Verify**: OpenAI API key is valid and has quota
   - **Check**: Internet connection stability
   - **Fallback**: System automatically switches to text mode

4. **High Latency**
   - **Optimize**: Reduce audio chunk size
   - **Network**: Check internet connection quality
   - **Settings**: Adjust volume controls

### Debug Information

The system provides extensive logging:

```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from app_enhanced import main
main()
"
```

## Performance Optimization

### Audio Settings

- **Sample Rate**: 16kHz (optimal for speech recognition)
- **Chunk Size**: 1024 samples (64ms chunks)
- **Buffer Size**: 120ms minimum for API compatibility
- **Volume Control**: Real-time adjustment via settings

### Network Optimization

- **WebSocket**: Persistent connection for low latency
- **Ping/Pong**: 20-second intervals for connection health
- **Reconnection**: Automatic recovery from disconnections

### Memory Management

- **Audio Queues**: Bounded queues prevent memory leaks
- **Thread Management**: Daemon threads for automatic cleanup
- **Resource Cleanup**: Proper disposal of audio streams

## Testing

### Automated Tests

Run the comprehensive test suite:

```bash
python test_speech_integration.py
```

Tests include:
- API connection and session creation
- Voice configuration for different NPCs
- Text-to-speech functionality
- Interruption handling
- Multi-NPC support
- Error recovery mechanisms

### Manual Testing

1. **Voice Mode Test**
   - Enable voice mode with 'V'
   - Speak a clear question
   - Verify NPC responds in voice and text

2. **Interruption Test**
   - Start a conversation
   - Press Space during NPC response
   - Verify interruption works smoothly

3. **Settings Test**
   - Open settings with ESC
   - Adjust volume sliders
   - Test voice previews

## Future Enhancements

### Planned Features

1. **Advanced Voice Customization**
   - Custom voice training for NPCs
   - Emotion detection and response
   - Accent and dialect support

2. **Multi-language Support**
   - Real-time language detection
   - Multi-language NPC responses
   - Translation capabilities

3. **Enhanced Interruption**
   - Context-aware interruption
   - Partial response handling
   - Conversation memory

4. **Performance Monitoring**
   - Latency metrics
   - Audio quality analysis
   - Network performance tracking

## Conclusion

The speech-to-speech integration successfully provides:

✅ **Real-time voice interaction** between players and NPCs  
✅ **Seamless text integration** maintaining existing functionality  
✅ **Dynamic voice personalities** for different NPCs  
✅ **Robust error handling** with graceful fallbacks  
✅ **User-friendly controls** with intuitive interface  
✅ **Comprehensive testing** ensuring reliability  

The implementation meets all assignment requirements and provides a solid foundation for future enhancements. 

---

# Reflection Report: Speech-to-Speech Integration in VBAIgame

## Overview
This assignment involved upgrading VBAIgame’s assistant from text-only to real-time speech-to-speech interaction using the OpenAI Realtime API. The goal was to allow players to converse naturally with NPCs using their voice, while maintaining seamless support for text input and ensuring low latency.

## Challenges Faced

### 1. Real-Time Audio Processing
- **Challenge:** Achieving low-latency, high-quality audio input and output.
- **Solution:** Used the `sounddevice` library for direct audio stream control. Tuned buffer sizes and ensured the playback thread always runs when needed.

### 2. WebSocket Reliability & API Integration
- **Challenge:** Maintaining a stable, low-latency connection with OpenAI’s Realtime API.
- **Solution:** Implemented robust connection logic, error callbacks, and automatic reconnection. Used async patterns for non-blocking communication.

### 3. Multi-Modal Interaction (Speech + Text)
- **Challenge:** Seamlessly supporting both speech and text input, with clear UI feedback to avoid user confusion.
- **Solution:** Ensured both input modes are always available. Improved UI prompts and overlays to indicate when the system is “Listening”, “Speaking”, or “Waiting for Input”.

### 4. NPC Voice Configuration
- **Challenge:** Making NPCs sound unique and contextually appropriate based on their roles.
- **Solution:** Used the `NPC_VOICES` dictionary in `config.py` to assign distinct voices and detailed instructions for each NPC. For example, Sarah Chen (HR) uses the "alloy" voice with a warm, supportive persona, and Michael Chen (CEO) uses the "echo" voice with confident, visionary instructions. All configurations were kept in sync with the codebase.

### 5. Interruptions Handling
- **Challenge:** Letting players interrupt NPC speech at any time.
- **Solution:** Added logic to instantly halt playback, clear audio buffers, and send a cancel message to the API. This ensures the system is always responsive to new input.

### 6. Audio Device & Volume Management
- **Challenge:** Supporting a variety of user hardware and preferences.
- **Solution:** Provided an in-game settings overlay for selecting input/output devices and adjusting volumes. Added debug output for device selection.

### 7. Bug: Dropped Audio When Playback Not Running
- **Challenge:** Sometimes, audio would not play if playback wasn’t already running.
- **Solution:** Fixed by updating `play_audio_chunk` to always start playback if not running, ensuring no audio is ever dropped.

## Solutions & What I Learned
- **API Nuances:** Real-time speech APIs require careful buffer management and error handling to avoid glitches.
- **User Experience:** Clear, immediate feedback is essential in voice-driven interfaces to avoid confusion.
- **NPC Configuration:** Keeping the configuration in code ensures maintainability and that documentation always matches the app's actual behavior.
- **Testing:** Both automated and manual playtesting are critical for robust speech features.
- **Flexibility:** Supporting both text and voice input ensures accessibility and player choice.
- **Problem-Solving:** Proactive debugging and iterative testing helped resolve tricky real-time and concurrency bugs.

## Outcome
- Players can now interact with NPCs using either voice or text, and always receive responses in both formats.
- Speech-to-speech works smoothly, with natural, character-specific NPC voices (as defined in code).
- Interruptions are handled gracefully, and device/volume settings are user-configurable.
- The system is robust, user-friendly, and ready for further expansion.