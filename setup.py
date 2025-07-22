#!/usr/bin/env python3
"""
BotBuddy Setup Script
Helps with initial setup and configuration
"""

import os
import sys

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All packages installed successfully")
            return True
        else:
            print(f"❌ Package installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"❌ {env_file} file not found")
        print("Please create a .env file with your API keys:")
        print("GEMINI_API_KEY=your_gemini_api_key_here")
        print("ELEVENLABS_API_KEY=your_elevenlabs_api_key_here")
        return False
    
    print("✅ .env file found")
    
    # Check if keys are present
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_keys = ['GEMINI_API_KEY', 'ELEVENLABS_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if key not in content or f"{key}=" not in content:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Missing API keys in .env: {', '.join(missing_keys)}")
        print("Please add these keys to your .env file")
        return False
    
    print("✅ Required API keys found in .env")
    return True

def check_data_files():
    """Check if required data files exist"""
    required_files = [
        'branches.json',
        'customers.json',
        'user_data.json',
        'session_data.json',
        'botbuddy_comprehensive_data.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file} found")
    
    if missing_files:
        print(f"❌ Missing data files: {', '.join(missing_files)}")
        print("Run 'python reset_data.py' to initialize missing files")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🤖 BotBuddy Setup & Configuration Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check environment file
    if not check_env_file():
        return False
    
    # Check data files
    print("\n📁 Checking data files...")
    if not check_data_files():
        print("\n💡 Tip: Run 'python reset_data.py' to initialize system")
        return False
    
    print("\n🎉 Setup complete! BotBuddy is ready to use.")
    print("\nTo start:")
    print("  - Voice Agent: python listen_agent.py")
    print("  - Text Agent:  python agent.py")
    print("\nOr use the provided batch files:")
    print("  - start_voice_agent.bat")
    print("  - start_text_agent.bat")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup incomplete. Please fix the issues above and try again.")
        sys.exit(1)
