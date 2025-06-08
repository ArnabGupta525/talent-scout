"""
Test script to debug Firestore connection issues.
Run this script to identify and fix Firestore problems.
"""

import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def test_firestore_connection():
    """Comprehensive Firestore connection test."""
    print("🔍 FIRESTORE CONNECTION DIAGNOSTIC")
    print("=" * 50)
    
    # Step 1: Check config file
    config_path = "config/firebase-credentials.json"
    print(f"1. Checking Firebase config file...")
    print(f"   📍 Path: {config_path}")
    print(f"   📁 Exists: {os.path.exists(config_path)}")
    
    if not os.path.exists(config_path):
        print("   ❌ Config file not found!")
        print("   💡 Make sure you have downloaded your Firebase service account key")
        print("   💡 and placed it at: config/firebase-credentials.json")
        return False
    
    # Step 2: Check config file content
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        print(f"   📋 Config file structure:")
        for field in required_fields:
            has_field = field in config_data
            print(f"      {field}: {'✅' if has_field else '❌'}")
            if not has_field:
                print(f"   ❌ Missing required field: {field}")
                return False
        
        project_id = config_data.get('project_id')
        print(f"   🆔 Project ID: {project_id}")
        
    except Exception as e:
        print(f"   ❌ Error reading config file: {e}")
        return False
    
    # Step 3: Initialize Firebase
    print(f"\n2. Initializing Firebase...")
    try:
        # Check if already initialized
        if firebase_admin._apps:
            print("   ℹ️ Firebase already initialized, deleting existing app...")
            firebase_admin.delete_app(firebase_admin.get_app())
        
        cred = credentials.Certificate(config_path)
        app = firebase_admin.initialize_app(cred)
        print("   ✅ Firebase initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Firebase initialization failed: {e}")
        return False
    
    # Step 4: Create Firestore client
    print(f"\n3. Creating Firestore client...")
    try:
        db = firestore.client()
        print("   ✅ Firestore client created")
        
    except Exception as e:
        print(f"   ❌ Firestore client creation failed: {e}")
        return False
    
    # Step 5: Test basic operations
    print(f"\n4. Testing Firestore operations...")
    
    # Test write
    try:
        test_collection = "connection_test"
        test_doc_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_data = {
            'message': 'Hello from test script',
            'timestamp': datetime.now().isoformat(),
            'test_number': 42
        }
        
        print(f"   📝 Writing test document...")
        print(f"      Collection: {test_collection}")
        print(f"      Document ID: {test_doc_id}")
        
        doc_ref = db.collection(test_collection).document(test_doc_id)
        doc_ref.set(test_data)
        print("   ✅ Test document written successfully")
        
    except Exception as e:
        print(f"   ❌ Write test failed: {e}")
        return False
    
    # Test read
    try:
        print(f"   📖 Reading test document...")
        doc = doc_ref.get()
        if doc.exists:
            print("   ✅ Test document read successfully")
            data = doc.to_dict()
            print(f"      Data: {data}")
        else:
            print("   ❌ Test document not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Read test failed: {e}")
        return False
    
    # Test query
    try:
        print(f"   🔍 Testing query...")
        collection_ref = db.collection(test_collection)
        docs = collection_ref.limit(5).stream()
        doc_count = len(list(docs))
        print(f"   ✅ Query successful, found {doc_count} documents")
        
    except Exception as e:
        print(f"   ❌ Query test failed: {e}")
        return False
    
    # Clean up test document
    try:
        print(f"   🗑️ Cleaning up test document...")
        doc_ref.delete()
        print("   ✅ Test document deleted")
        
    except Exception as e:
        print(f"   ⚠️ Cleanup failed (not critical): {e}")
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"✅ Firestore is properly configured and working")
    return True

def test_candidates_collection():
    """Test the candidates collection specifically."""
    print(f"\n🔍 TESTING CANDIDATES COLLECTION")
    print("=" * 50)
    
    try:
        db = firestore.client()
        
        # Test saving a candidate
        candidate_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'experience_years': 5,
            'desired_positions': ['Software Engineer'],
            'location': 'Test City',
            'tech_stack': {
                'Programming Languages': ['Python', 'JavaScript'],
                'Frameworks': ['React', 'Django']
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'session_id': 'test_session_123'
        }
        
        print("📝 Saving test candidate...")
        doc_ref = db.collection('candidates').document('test_session_123')
        doc_ref.set(candidate_data)
        print("✅ Test candidate saved")
        
        # Read it back
        print("📖 Reading test candidate...")
        doc = doc_ref.get()
        if doc.exists:
            print("✅ Test candidate read successfully")
            data = doc.to_dict()
            print(f"📄 Candidate name: {data.get('full_name')}")
            print(f"📧 Email: {data.get('email')}")
        else:
            print("❌ Test candidate not found")
            return False
        
        # List all candidates
        print("📋 Listing all candidates...")
        candidates_ref = db.collection('candidates')
        docs = candidates_ref.stream()
        candidate_count = 0
        for doc in docs:
            candidate_count += 1
            data = doc.to_dict()
            print(f"   📄 {doc.id}: {data.get('full_name', 'No name')}")
        
        print(f"📊 Total candidates in database: {candidate_count}")
        
        # Clean up test candidate
        print("🗑️ Cleaning up test candidate...")
        doc_ref.delete()
        print("✅ Test candidate deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Candidates collection test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 STARTING FIRESTORE DIAGNOSTIC TESTS")
    print("=" * 60)
    
    # Test basic connection
    if not test_firestore_connection():
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("1. Make sure you have the correct Firebase service account key")
        print("2. Check that the key file is in config/firebase-credentials.json")
        print("3. Verify your Firebase project has Firestore enabled")
        print("4. Check your internet connection")
        print("5. Ensure your Firebase project allows API access")
        return
    
    # Test candidates collection
    if not test_candidates_collection():
        print("\n💡 CANDIDATES COLLECTION ISSUES:")
        print("1. Check Firestore security rules")
        print("2. Verify collection name is correct")
        print("3. Check if you have write permissions")
        return
    
    print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("✅ Your Firestore setup is working correctly")
    print("✅ The candidates collection is functional")
    print("\nYour application should now be able to save data to Firestore.")

if __name__ == "__main__":
    main()