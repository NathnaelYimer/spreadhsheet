#!/usr/bin/env python3
"""
Quick test to verify setup before running the main game
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import pygame
        print("✓ pygame imported successfully")
    except ImportError as e:
        print(f"✗ pygame import failed: {e}")
        return False
    
    try:
        import OpenGL.GL
        print("✓ OpenGL imported successfully")
    except ImportError as e:
        print(f"✗ OpenGL import failed: {e}")
        return False
    
    try:
        import sounddevice as sd
        print("✓ sounddevice imported successfully")
    except ImportError as e:
        print(f"✗ sounddevice import failed: {e}")
        return False
    
    try:
        import websockets
        print("✓ websockets imported successfully")
    except ImportError as e:
        print(f"✗ websockets import failed: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("✓ openai imported successfully")
    except ImportError as e:
        print(f"✗ openai import failed: {e}")
        return False
    
    return True

def test_api_key():
    """Test if API key is loaded correctly"""
    print("\nTesting API key...")
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("✗ OPENAI_API_KEY not found in environment")
        return False
    
    if not api_key.startswith('sk-'):
        print("✗ API key doesn't appear to be valid (should start with 'sk-')")
        return False
    
    print(f"✓ API key loaded: {api_key[:20]}...")
    return True

def test_audio_system():
    """Test audio system"""
    print("\nTesting audio system...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        output_devices = [d for d in devices if d.get('max_output_channels', 0) > 0]
        
        print(f"✓ Found {len(input_devices)} input device(s)")
        print(f"✓ Found {len(output_devices)} output device(s)")
        
        if len(input_devices) == 0:
            print("⚠ Warning: No microphone detected")
        if len(output_devices) == 0:
            print("⚠ Warning: No speakers detected")
        
        return True
        
    except Exception as e:
        print(f"✗ Audio system test failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\nTesting OpenAI connection...")
    
    try:
        load_dotenv()
        from openai import OpenAI
        
        # Use the modern client-based API without any proxy settings
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), http_client=None)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("✓ OpenAI API connection successful")
        print(f"✓ Test response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"✗ OpenAI API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("VBAIgame Setup Test")
    print("=" * 30)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test API key
    if not test_api_key():
        all_passed = False
    
    # Test audio
    if not test_audio_system():
        all_passed = False
    
    # Test OpenAI connection
    if not test_openai_connection():
        all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("🎉 All tests passed! You're ready to run the game.")
        print("\nRun the game with: python app_enhanced.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
