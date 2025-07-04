#!/usr/bin/env python3
"""
Script to verify Firebase service account file path and contents
Run this before starting your main application
"""

import os
import json
from pathlib import Path

def check_firebase_file():
    print("🔍 Firebase Service Account File Checker")
    print("=" * 50)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # List all JSON files in current directory
    json_files = list(Path('.').glob('*.json'))
    print(f"\n📋 JSON files found: {len(json_files)}")
    for file in json_files:
        print(f"  - {file}")
    
    # Check common file names
    common_names = [
        "firebase-service-account.json",
        "service-account.json",
        "serviceAccountKey.json"
    ]
    
    found_files = []
    for name in common_names:
        if os.path.exists(name):
            found_files.append(name)
    
    if found_files:
        print(f"\n✅ Found common Firebase files:")
        for file in found_files:
            print(f"  - {file}")
    else:
        print(f"\n❌ No common Firebase files found")
    
    # Check for any file with 'firebase' in the name
    firebase_files = list(Path('.').glob('*firebase*.json'))
    if firebase_files:
        print(f"\n🔥 Files with 'firebase' in name:")
        for file in firebase_files:
            print(f"  - {file}")
    
    # If we found files, let's test them
    test_files = found_files + [str(f) for f in firebase_files]
    
    if test_files:
        print(f"\n🧪 Testing Firebase files:")
        for file_path in test_files:
            test_firebase_file(file_path)
    else:
        print(f"\n❌ No Firebase service account files found!")
        print("📝 To fix this:")
        print("1. Download your Firebase service account key from Firebase Console")
        print("2. Place it in this directory:")
        print(f"   {current_dir}")
        print("3. Name it 'firebase-service-account.json' or update your .env file")

def test_firebase_file(file_path):
    print(f"\n  Testing: {file_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"    ❌ File not found")
            return
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"    📏 File size: {file_size} bytes")
        
        if file_size == 0:
            print(f"    ❌ File is empty")
            return
        
        # Try to read as JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"    ✅ Valid JSON")
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"    ❌ Missing required fields: {missing_fields}")
        else:
            print(f"    ✅ All required fields present")
            print(f"    📋 Project ID: {data.get('project_id')}")
            print(f"    📧 Client Email: {data.get('client_email')}")
        
        # Generate .env entry
        abs_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(file_path)
        
        print(f"    📝 For your .env file, use:")
        print(f"      FIREBASE_SERVICE_ACCOUNT_PATH={rel_path}")
        print(f"    📝 Or absolute path:")
        print(f"      FIREBASE_SERVICE_ACCOUNT_PATH={abs_path}")
        
    except json.JSONDecodeError as e:
        print(f"    ❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"    ❌ Error reading file: {e}")

if __name__ == "__main__":
    check_firebase_file()