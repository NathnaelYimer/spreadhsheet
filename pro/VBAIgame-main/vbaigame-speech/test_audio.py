# Create a simple test file: test_audio.py
import sounddevice as sd
import numpy as np

print("Testing audio system...")

# List available audio devices
print("\nAvailable audio devices:")
print(sd.query_devices())

# Test recording
print("\nTesting microphone (speak for 3 seconds)...")
duration = 3
sample_rate = 24000

try:
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    print("✓ Microphone test successful")
    
    # Test playback
    print("Playing back recording...")
    sd.play(recording, sample_rate)
    sd.wait()
    print("✓ Speaker test successful")
    
except Exception as e:
    print(f"Audio test failed: {e}")