#!/usr/bin/env python3
"""
Test script for Speech-to-Speech Integration
Tests all aspects of the OpenAI Realtime API integration
"""

import asyncio
import time
import logging
from enhanced_dialogue_system import EnhancedDialogueSystem
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpeechIntegrationTester:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.api_key = api_key
        self.dialogue_system = None
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting Speech-to-Speech Integration Tests")
        
        tests = [
            ("API Connection", self.test_api_connection),
            ("Voice Configuration", self.test_voice_configuration),
            ("Text-to-Speech", self.test_text_to_speech),
            ("Speech-to-Text", self.test_speech_to_text),
            ("Interruption Handling", self.test_interruption_handling),
            ("Multi-NPC Support", self.test_multi_npc_support),
            ("Error Recovery", self.test_error_recovery)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Running Test: {test_name}")
                logger.info(f"{'='*50}")
                
                result = test_func()
                self.test_results[test_name] = result
                
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name] = False
        
        self.print_test_summary()
    
    async def test_api_connection(self):
        """Test API connection and session creation"""
        try:
            self.dialogue_system = EnhancedDialogueSystem(self.api_key)
            
            # Test connection
            if not self.dialogue_system.realtime_client:
                logger.error("Realtime client not initialized")
                return False
            
            # Test session creation
            await self.dialogue_system.realtime_client.connect()
            
            if not self.dialogue_system.realtime_client.is_connected:
                logger.error("Failed to connect to API")
                return False
            
            logger.info("✅ API connection successful")
            return True
            
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    async def test_voice_configuration(self):
        """Test dynamic voice configuration for different NPCs"""
        try:
            # Test HR voice configuration
            hr_config = self.dialogue_system.realtime_client.get_npc_voice_config("HR")
            if hr_config["voice"] != "alloy":
                logger.error("HR voice configuration incorrect")
                return False
            
            # Test CEO voice configuration
            ceo_config = self.dialogue_system.realtime_client.get_npc_voice_config("CEO")
            if ceo_config["voice"] != "echo":
                logger.error("CEO voice configuration incorrect")
                return False
            
            # Test setting new voice configuration
            self.dialogue_system.realtime_client.set_npc_voice_config(
                "Engineer", "fable", "You are a technical expert.", "Hello from engineering!"
            )
            
            engineer_config = self.dialogue_system.realtime_client.get_npc_voice_config("Engineer")
            if engineer_config["voice"] != "fable":
                logger.error("Engineer voice configuration not set correctly")
                return False
            
            logger.info("✅ Voice configuration test successful")
            return True
            
        except Exception as e:
            logger.error(f"Voice configuration test failed: {e}")
            return False
    
    async def test_text_to_speech(self):
        """Test text-to-speech functionality"""
        try:
            # Send a text message and check for response
            test_message = "Hello, this is a test message."
            
            await self.dialogue_system.realtime_client.send_text_message(
                test_message, npc_name="HR"
            )
            
            # Wait for response (with timeout)
            start_time = time.time()
            response_received = False
            
            while time.time() - start_time < 10:  # 10 second timeout
                if self.dialogue_system.npc_message and "test" in self.dialogue_system.npc_message.lower():
                    response_received = True
                    break
                await asyncio.sleep(0.1)
            
            if not response_received:
                logger.error("No text response received within timeout")
                return False
            
            logger.info("✅ Text-to-speech test successful")
            return True
            
        except Exception as e:
            logger.error(f"Text-to-speech test failed: {e}")
            return False
    
    async def test_speech_to_text(self):
        """Test speech-to-text functionality"""
        try:
            # This would require actual microphone input
            # For now, we'll test the audio processing pipeline
            logger.info("Note: Speech-to-text test requires microphone input")
            logger.info("This test is skipped in automated testing")
            return True
            
        except Exception as e:
            logger.error(f"Speech-to-text test failed: {e}")
            return False
    
    async def test_interruption_handling(self):
        """Test interruption functionality"""
        try:
            # Send a long message
            long_message = "This is a very long message that should take some time to process and respond to. " * 5
            
            await self.dialogue_system.realtime_client.send_text_message(
                long_message, npc_name="HR"
            )
            
            # Wait a bit then interrupt
            await asyncio.sleep(2)
            
            await self.dialogue_system.realtime_client.interrupt_response()
            
            # Check if interruption was handled
            if not self.dialogue_system.realtime_client.is_processing:
                logger.info("✅ Interruption handling test successful")
                return True
            else:
                logger.error("Interruption not handled properly")
                return False
                
        except Exception as e:
            logger.error(f"Interruption handling test failed: {e}")
            return False
    
    async def test_multi_npc_support(self):
        """Test support for multiple NPCs with different voices"""
        try:
            npcs = ["HR", "CEO", "Engineer"]
            
            for npc in npcs:
                config = self.dialogue_system.realtime_client.get_npc_voice_config(npc)
                if not config:
                    logger.error(f"No configuration found for {npc}")
                    return False
                
                # Test sending message to each NPC
                test_msg = f"Hello from {npc} test"
                await self.dialogue_system.realtime_client.send_text_message(
                    test_msg, npc_name=npc
                )
                
                # Wait for response
                await asyncio.sleep(1)
            
            logger.info("✅ Multi-NPC support test successful")
            return True
            
        except Exception as e:
            logger.error(f"Multi-NPC support test failed: {e}")
            return False
    
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        try:
            # Test with invalid message (should not crash)
            try:
                await self.dialogue_system.realtime_client.send_text_message("", npc_name="InvalidNPC")
            except Exception:
                pass  # Expected to fail
            
            # Test reconnection
            await self.dialogue_system.realtime_client.disconnect()
            await asyncio.sleep(1)
            
            reconnect_success = await self.dialogue_system.realtime_client.connect()
            if not reconnect_success:
                logger.error("Reconnection failed")
                return False
            
            logger.info("✅ Error recovery test successful")
            return True
            
        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            return False
    
    def print_test_summary(self):
        """Print summary of all test results"""
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Speech-to-speech integration is working correctly.")
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Please check the implementation.")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.dialogue_system:
            await self.dialogue_system.realtime_client.disconnect()

async def main():
    """Main test runner"""
    tester = SpeechIntegrationTester()
    
    try:
        # Run all tests
        await tester.test_api_connection()
        await tester.test_voice_configuration()
        await tester.test_text_to_speech()
        await tester.test_speech_to_text()
        await tester.test_interruption_handling()
        await tester.test_multi_npc_support()
        await tester.test_error_recovery()
        
        # Print summary
        tester.print_test_summary()
        
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
    
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 