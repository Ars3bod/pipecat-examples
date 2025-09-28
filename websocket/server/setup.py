#!/usr/bin/env python3
#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Setup script for Arabic-First Organizational AI Agent.
This script helps configure the environment and test the setup.
"""

import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment configuration."""
    print("🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from env.example")
        else:
            print("❌ env.example not found!")
            return False
    else:
        print("ℹ️  .env file already exists")
    
    return True

def get_user_input():
    """Get user input for configuration."""
    print("\n📝 Please provide the following information:")
    
    # Google API Key
    google_key = input("Enter your Google API Key (or press Enter to skip): ").strip()
    
    # Organization Name
    org_name = input("Enter your organization name (or press Enter for default): ").strip()
    if not org_name:
        org_name = "الهيئة"
    
    # Assistant Name
    assistant_name = input("Enter your assistant's name (or press Enter for default): ").strip()
    if not assistant_name:
        assistant_name = "مساعد الهيئة"
    
    # Server Mode
    print("\nSelect server mode:")
    print("1. FastAPI WebSocket (recommended)")
    print("2. Standalone WebSocket Server")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            server_mode = "fast_api"
            break
        elif choice == "2":
            server_mode = "websocket_server"
            break
        else:
            print("Please enter 1 or 2")
    
    return google_key, org_name, assistant_name, server_mode

def update_env_file(google_key, org_name, assistant_name, server_mode):
    """Update the .env file with user input."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update values
    updated_lines = []
    for line in lines:
        if line.startswith("GOOGLE_API_KEY="):
            if google_key:
                updated_lines.append(f"GOOGLE_API_KEY={google_key}\n")
            else:
                updated_lines.append(line)
        elif line.startswith("WEBSOCKET_SERVER="):
            updated_lines.append(f"WEBSOCKET_SERVER={server_mode}\n")
        elif line.startswith("ORGANIZATION_NAME="):
            updated_lines.append(f"ORGANIZATION_NAME={org_name}\n")
        elif line.startswith("ASSISTANT_NAME="):
            updated_lines.append(f"ASSISTANT_NAME={assistant_name}\n")
        else:
            updated_lines.append(line)
    
    # Write back
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print("✅ Updated .env file")
    return True

def test_setup():
    """Test the setup by running the test suite."""
    print("\n🧪 Testing the setup...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_arabic_config.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Setup test passed!")
            return True
        else:
            print("❌ Setup test failed!")
            print("Error output:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def show_next_steps():
    """Show next steps to the user."""
    print("\n🚀 Setup Complete! Next Steps:")
    print("=" * 50)
    print("1. Start the server:")
    print("   python server.py")
    print()
    print("2. Test with WebSocket client:")
    print("   Connect to: ws://localhost:7860/ws")
    print()
    print("3. Test Arabic voice input:")
    print("   - Speak in Arabic (Saudi accent)")
    print("   - Ask about HR policies, IT support, etc.")
    print("   - Verify agent responds in Arabic")
    print()
    print("4. Test English fallback:")
    print("   - Say 'speak English' or 'تحدث بالإنجليزية'")
    print("   - Verify agent switches to English")
    print()
    print("5. Test organizational scope:")
    print("   - Ask work-related questions (should work)")
    print("   - Ask about weather/sports (should decline)")
    print()
    print("📚 For more information, see README.md")

def main():
    """Main setup function."""
    print("🚀 Arabic-First Organizational AI Agent - Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("server.py").exists():
        print("❌ Please run this script from the server directory")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment")
        sys.exit(1)
    
    # Get user input
    google_key, org_name, assistant_name, server_mode = get_user_input()
    
    # Update .env file
    if not update_env_file(google_key, org_name, assistant_name, server_mode):
        print("❌ Failed to update .env file")
        sys.exit(1)
    
    # Test setup
    if not test_setup():
        print("⚠️  Setup test failed, but you can still try running the server")
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
