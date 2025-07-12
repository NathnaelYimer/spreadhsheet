# VBAIgame Speech-to-Speech Integration

This project enhances the VBAIgame experience by enabling real-time, low-latency speech-to-speech interaction between players and NPCs using the OpenAI Realtime API. Players can interact with NPCs by speaking or typing, and NPCs respond in both voice and text.

## Features
- --Real-Time Speech-to-Speech--: Speak naturally to NPCs; receive instant, natural-sounding voice and text responses.
- --Seamless Text Integration--: The text box remains fully functional; type or speak at any time.
- --Dynamic NPC Voices--: Each NPC has a unique, configurable AI voice (e.g., alloy, echo).
- --Interruptions--: Press `Space` to interrupt NPC speech and provide new input.
- --Audio Settings--: In-game overlay for microphone/speaker selection and volume control.

## Quick Start
1. --Install dependencies:--
   ```sh
   pip install -r requirements_enhanced.txt
   ```
2. --Set your OpenAI API key:--
   - Add your key to a `.env` file:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```
3. --Run the game:--
   ```sh
   python app_enhanced.py
   ```

## Controls
- --V--: Start/stop voice input
- --Enter--: Send typed message
- --Space--: Interrupt NPC speech
- --ESC--: Open/close settings overlay

## Troubleshooting
- Ensure your microphone and speakers are connected and selected in settings.
- For API or audio errors, check the terminal for debug info.

## License
MIT

---
For more details, see the full reflection report in `REFLECTION_REPORT.md`.
