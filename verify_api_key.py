#!/usr/bin/env python3
"""
Simple verification script to test that the Gemini API key is correctly configured.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_key_configuration():
    """Test that API key is properly configured across all modules"""
    
    print("🔑 TESTING GEMINI API KEY CONFIGURATION")
    print("=" * 50)
    
    # Test 1: Check agent.py
    try:
        from agent import api_key as agent_api_key
        print(f"✅ agent.py API key: {agent_api_key[:20]}...")
        assert agent_api_key == "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
        print("✅ agent.py API key is correct")
    except Exception as e:
        print(f"❌ agent.py API key test failed: {e}")
    
    # Test 2: Check listen_agent.py VoiceAgent
    try:
        from listen_agent import VoiceAgent
        voice_agent = VoiceAgent()
        print(f"✅ VoiceAgent API key: {voice_agent.api_key[:20]}...")
        assert voice_agent.api_key == "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
        print("✅ VoiceAgent API key is correct")
    except Exception as e:
        print(f"❌ VoiceAgent API key test failed: {e}")
    
    # Test 3: Check gemini_api.py functionality
    try:
        from gemini_api import send_to_gemini
        test_response = send_to_gemini("Say 'API test successful'", "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM")
        print(f"✅ Gemini API response: {test_response[:50]}...")
        print("✅ Gemini API is working correctly")
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
    
    # Test 4: Check keys.json
    try:
        import json
        with open('keys.json', 'r') as f:
            keys = json.load(f)
        if 'gemini_api_key' in keys:
            print(f"✅ keys.json gemini_api_key: {keys['gemini_api_key'][:20]}...")
            assert keys['gemini_api_key'] == "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
            print("✅ keys.json is correctly configured")
        else:
            print("⚠️ keys.json doesn't contain gemini_api_key")
    except Exception as e:
        print(f"❌ keys.json test failed: {e}")
    
    # Test 5: Check .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        env_api_key = os.getenv('GEMINI_API_KEY')
        if env_api_key:
            print(f"✅ .env GEMINI_API_KEY: {env_api_key[:20]}...")
            assert env_api_key == "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
            print("✅ .env file is correctly configured")
        else:
            print("⚠️ .env file doesn't contain GEMINI_API_KEY")
    except Exception as e:
        print(f"❌ .env file test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API KEY CONFIGURATION TEST COMPLETE")
    print("\nExpected API Key: AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM")
    print("All modules should now use this hardcoded API key for reliability.")

if __name__ == "__main__":
    test_api_key_configuration()
