#!/usr/bin/env python3
"""
Setup script for VBAIgame Speech-to-Speech Integration
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_enhanced.txt"])
        print("✓ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

def check_audio_system():
    """Check if audio system is available"""
    try:
        import sounddevice as sd
        # Test audio devices
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        output_devices = [d for d in devices if d['max_output_channels'] > 0]
        
        if not input_devices:
            print("Warning: No input audio devices found")
        else:
            print(f"✓ Found {len(input_devices)} input audio device(s)")
        
        if not output_devices:
            print("Warning: No output audio devices found")
        else:
            print(f"✓ Found {len(output_devices)} output audio device(s)")
            
    except Exception as e:
        print(f"Warning: Could not check audio system: {e}")

def setup_environment():
    """Setup environment file"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("# OpenAI API Configuration\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("OPENAI_REALTIME_API_KEY=your_realtime_api_key_here\n")
            f.write("\n# Logging\n")
            f.write("LOG_LEVEL=INFO\n")
        print("✓ Created .env file - please add your API keys")
    else:
        print("✓ .env file already exists")

def check_opengl():
    """Check OpenGL availability"""
    try:
        import pygame
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.OPENGL)
        from OpenGL.GL import glGetString, GL_VERSION
        version = glGetString(GL_VERSION)
        print(f"✓ OpenGL {version.decode()} available")
        pygame.quit()
    except Exception as e:
        print(f"Warning: OpenGL check failed: {e}")

def main():
    """Main setup function"""
    print("VBAIgame Speech-to-Speech Integration Setup")
    print("=" * 50)
    
    # Check system requirements
    check_python_version()
    
    # Install requirements
    install_requirements()
    
    # Check audio system
    check_audio_system()
    
    # Check OpenGL
    check_opengl()
    
    # Setup environment
    setup_environment()
    
    print("\n" + "=" * 50)
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Add your OpenAI API keys to the .env file")
    print("2. Run the game with: python app_enhanced.py")
    print("\nControls:")
    print("- WASD: Move around")
    print("- Mouse: Look around")
    print("- V: Toggle voice mode when talking to NPCs")
    print("- Space: Interrupt NPC speech")
    print("- Shift+Q: Exit conversation")
    print("- ESC: Exit game")

if __name__ == "__main__":
    main()
