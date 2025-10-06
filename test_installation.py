#!/usr/bin/env python3
"""
Test script to verify Pundora installation and functionality.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False
    
    try:
        import elevenlabs
        print("✅ ElevenLabs imported successfully")
    except ImportError as e:
        print(f"❌ ElevenLabs import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✅ Pydantic imported successfully")
    except ImportError as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    return True

def test_project_structure():
    """Test if project structure is correct."""
    print("\n📁 Testing project structure...")
    
    required_files = [
        "pundora/__init__.py",
        "pundora/api.py",
        "pundora/cli.py",
        "pundora/config.py",
        "pundora/joke_generator.py",
        "pundora/tts_service.py",
        "templates/index.html",
        "main.py",
        "requirements.txt",
        ".env.example"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from pundora.config import config
        print("✅ Configuration loaded successfully")
        print(f"   - Host: {config.HOST}")
        print(f"   - Port: {config.PORT}")
        print(f"   - Debug: {config.DEBUG}")
        print(f"   - Categories: {len(config.CATEGORIES)}")
        print(f"   - Humor levels: {len(config.HUMOR_LEVELS)}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_joke_generator():
    """Test joke generator functionality."""
    print("\n🎭 Testing joke generator...")
    
    try:
        from pundora.joke_generator import JokeGenerator
        
        # Test without API key (fallback mode)
        generator = JokeGenerator()
        print("✅ Joke generator initialized")
        
        # Test fallback joke generation
        result = await generator.generate_joke("general", "medium")
        print(f"✅ Generated joke: {result['joke'][:50]}...")
        print(f"   - Category: {result['category']}")
        print(f"   - Humor level: {result['humor_level']}")
        print(f"   - Source: {result['source']}")
        
        return True
    except Exception as e:
        print(f"❌ Joke generator test failed: {e}")
        return False

def test_cli():
    """Test CLI functionality."""
    print("\n💻 Testing CLI...")
    
    try:
        # Test help command
        result = subprocess.run([
            sys.executable, "-m", "pundora.cli", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ CLI help command works")
        else:
            print(f"❌ CLI help command failed: {result.stderr}")
            return False
        
        # Test list categories
        result = subprocess.run([
            sys.executable, "-m", "pundora.cli", "--list-categories"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ CLI list categories works")
        else:
            print(f"❌ CLI list categories failed: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def test_api_imports():
    """Test API module imports."""
    print("\n🌐 Testing API imports...")
    
    try:
        from pundora.api import app
        print("✅ FastAPI app imported successfully")
        
        # Test if routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/api/health", "/api/joke", "/api/voice"]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} not found")
                return False
        
        return True
    except Exception as e:
        print(f"❌ API import test failed: {e}")
        return False

def test_web_template():
    """Test web template."""
    print("\n🎨 Testing web template...")
    
    try:
        template_path = "templates/index.html"
        if not os.path.exists(template_path):
            print(f"❌ Template file not found: {template_path}")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key elements
        required_elements = [
            "Pundora",
            "Generate Joke",
            "category",
            "humorLevel",
            "voiceType"
        ]
        
        for element in required_elements:
            if element in content:
                print(f"✅ Template contains: {element}")
            else:
                print(f"❌ Template missing: {element}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🎭 Pundora Installation Test")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Configuration", test_configuration),
        ("Imports", test_imports),
        ("API Imports", test_api_imports),
        ("Web Template", test_web_template),
        ("Joke Generator", test_joke_generator),
        ("CLI", test_cli),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pundora is ready to use!")
        print("\n🚀 Quick start:")
        print("   1. Copy .env.example to .env and add your API keys")
        print("   2. Run: python main.py")
        print("   3. Open: http://localhost:8000")
        print("   4. Or use CLI: pundora --joke")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())