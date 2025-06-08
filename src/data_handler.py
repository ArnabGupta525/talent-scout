"""Enhanced data handling with environment variables for Firebase configuration."""

import json
import os
import re
import validators
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from pydantic import BaseModel, EmailStr, validator
import firebase_admin
from firebase_admin import credentials, firestore
from difflib import SequenceMatcher


class CandidateData(BaseModel):
    """Pydantic model for candidate data validation."""
    
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    desired_positions: Optional[List[str]] = None
    location: Optional[str] = None
    tech_stack: Optional[Dict[str, List[str]]] = None
    interview_responses: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    session_id: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and not validators.email(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v
    
    @validator('experience_years')
    def validate_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError('Experience years must be between 0 and 50')
        return v

class DataHandler:
    """Handles candidate data storage with Firestore and duplicate checking."""
    
    def __init__(self):
        
        self.db = None
        self.collection_name = "candidates"
        self.firebase_initialized = False
        
        # Initialize Firebase/Firestore using environment variables
        self._initialize_firebase_from_env()
    
    def _initialize_firebase_from_env(self):
        """Initialize Firebase using environment variables."""
        print(f"🔍 Initializing Firebase from environment variables...")
        
        # Check for required environment variables
        required_env_vars = [
            'FIREBASE_TYPE',
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL',
            'FIREBASE_CLIENT_ID',
            'FIREBASE_AUTH_URI',
            'FIREBASE_TOKEN_URI'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("❌ Firebase initialization skipped")
            return
        
        try:
            print("📋 All required environment variables found")
            
            # Create credentials dictionary from environment variables
            firebase_config = {
                "type": os.getenv('FIREBASE_TYPE'),
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),  # Handle escaped newlines
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
                "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            }
            
            print(f"🔍 Firebase config created for project: {firebase_config['project_id']}")
            print(f"📧 Using service account: {firebase_config['client_email']}")
            
            # Check if Firebase app is already initialized
            print(f"🔍 Current Firebase apps: {len(firebase_admin._apps)}")
            
            if not firebase_admin._apps:
                print("🚀 Initializing new Firebase app...")
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase app initialized")
            else:
                print("ℹ️ Firebase app already initialized")
            
            # Initialize Firestore client
            print("🔍 Initializing Firestore client...")
            self.db = firestore.client()
            print("✅ Firestore client created")
            
            # Test connection with more detailed output
            print("🧪 Testing Firestore connection...")
            self._test_firestore_connection()
            
            self.firebase_initialized = True
            print("✅ Firestore fully initialized and tested")
            
        except Exception as e:
            print(f"❌ Firebase initialization error: {type(e).__name__}: {e}")
            print(f"📊 Error details: {str(e)}")
            
            # Additional debugging for common issues
            if "private_key" in str(e).lower():
                print("💡 Hint: Check if FIREBASE_PRIVATE_KEY has proper newline characters")
                print("💡 Make sure the private key is wrapped in quotes in your .env file")
            elif "project_id" in str(e).lower():
                print("💡 Hint: Verify your FIREBASE_PROJECT_ID is correct")
            elif "client_email" in str(e).lower():
                print("💡 Hint: Check your FIREBASE_CLIENT_EMAIL format")
                
            self.db = None
            self.firebase_initialized = False

    def _test_firestore_connection(self):
        """Enhanced Firestore connection test."""
        if not self.db:
            print("❌ No Firestore client to test")
            return
            
        try:
            print("🔍 Testing basic Firestore operations...")
            
            # Test 1: Try to access collections
            collections = self.db.collections()
            collection_names = [col.id for col in collections]
            print(f"📋 Available collections: {collection_names}")
            
            # Test 2: Try to write a test document
            test_ref = self.db.collection('connection_test').document('test_doc')
            test_data = {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connection test successful',
                'initialized_from': 'environment_variables'
            }
            
            print("📝 Writing test document...")
            test_ref.set(test_data)
            print("✅ Test document written successfully")
            
            # Test 3: Try to read the test document
            print("📖 Reading test document...")
            doc = test_ref.get()
            if doc.exists:
                print("✅ Test document read successfully")
                print(f"📄 Test document data: {doc.to_dict()}")
                
                # Clean up test document
                test_ref.delete()
                print("🗑️ Test document cleaned up")
            else:
                print("❌ Test document not found after write")
                
        except Exception as e:
            print(f"❌ Firestore connection test failed: {type(e).__name__}: {e}")
            raise e
    
    
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        if not phone:
            return ""
        return re.sub(r'\D', '', str(phone))[-10:]  # Last 10 digits

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        if not name:
            return ""
        return re.sub(r'[^a-zA-Z]', '', str(name)).lower()
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def check_duplicate_candidate(self, candidate_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if candidate already exists based on name, email, or phone."""
        if not self.db or not self.firebase_initialized:
            return False, "Firestore not available for duplicate check"
    
        try:
            new_name = self._normalize_name(candidate_data.get('full_name', ''))
            new_email = candidate_data.get('email', '').lower().strip()
            new_phone = self._normalize_phone(candidate_data.get('phone', ''))
        
            candidates_ref = self.db.collection(self.collection_name)
        
            # Check email duplicates
            if new_email:
                email_query = candidates_ref.where('email', '==', new_email).limit(1)
                email_docs = list(email_query.stream())
                if email_docs:
                    return True, f"Email {new_email} already registered"
        
            # Check phone and name duplicates by scanning all candidates
            if new_phone or new_name:
                all_candidates = candidates_ref.stream()
                for doc in all_candidates:
                    existing = doc.to_dict()
                
                    # Phone check
                    if new_phone:
                        existing_phone = self._normalize_phone(existing.get('phone', ''))
                        if existing_phone and existing_phone == new_phone:
                            return True, f"Phone number already registered"
                
                    # Name similarity check
                    if new_name:
                        existing_name = self._normalize_name(existing.get('full_name', ''))
                        if existing_name and self._similarity_score(new_name, existing_name) > 0.85:
                            return True, f"Similar name already exists: {existing.get('full_name')}"
        
            return False, ""
        
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return False, f"Error checking duplicates: {e}"
    
    def save_candidate(self, candidate_data: Dict[str, Any], session_id: str) -> Tuple[bool, str]:
        """Save candidate to Firestore only."""
        print(f"\n🚀 Starting candidate save process...")
        print(f"📋 Session ID: {session_id}")
        print(f"📊 Candidate data keys: {list(candidate_data.keys())}")
        print(f"🔥 Firestore initialized: {self.firebase_initialized}")
        print(f"🔗 Firestore client exists: {self.db is not None}")
    
        if not self.db or not self.firebase_initialized:
            error_msg = "Firestore not initialized - cannot save candidate"
            print(f"❌ {error_msg}")
            return False, error_msg
    
        try:
            # Check for duplicates first
            print("🔍 Checking for duplicates...")
            is_duplicate, duplicate_msg = self.check_duplicate_candidate(candidate_data)
            if is_duplicate:
                print(f"❌ Duplicate found: {duplicate_msg}")
                return False, f"Duplicate candidate detected: {duplicate_msg}"
            print("✅ No duplicates found")
        
            # Validate data
            print("🔍 Validating candidate data...")
            candidate = CandidateData(**candidate_data)
            candidate.session_id = session_id
            candidate.created_at = datetime.now().isoformat()
            candidate.updated_at = datetime.now().isoformat()
        
            candidate_dict = candidate.dict()
            print("✅ Data validation successful")
        
            # Save to Firestore only
            print(f"🔥 Attempting Firestore save to collection: {self.collection_name}")
            print(f"📄 Document ID: {session_id}")
        
            #  Use session_id as document ID for easy retrieval
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            print(f"📍 Document reference created: {doc_ref.path}")
        
            # Set the document
            print("📝 Writing document to Firestore...")
            doc_ref.set(candidate_dict)
            print("✅ Document write completed")
        
            # Verify the write by reading back
            print("🔍 Verifying write by reading document...")
            saved_doc = doc_ref.get()
            if saved_doc.exists:
                print("✅ Document verified - exists in Firestore")
                saved_data = saved_doc.to_dict()
                print(f"📄 Saved document keys: {list(saved_data.keys())}")
            
                success_msg = "Candidate saved successfully to Firestore"
                print(f"🎉 {success_msg}")
                return True, success_msg
            else:
                error_msg = "Document verification failed - not found after write"
                print(f"❌ {error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Error saving candidate: {type(e).__name__}: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def get_candidate_by_session(self, session_id: str) -> Optional[Dict]:
        """Get candidate data by session ID from Firestore only."""
        if not self.db or not self.firebase_initialized:
            print("❌ Firestore not available")
            return None
    
        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc = doc_ref.get()
            if doc.exists:
                print(f"📖 Retrieved from Firestore: {session_id}")
                return doc.to_dict()
            else:
                print(f"❌ Candidate not found: {session_id}")
                return None
        except Exception as e:
            print(f"❌ Firestore get error: {e}")
            return None

    def get_all_candidates(self, limit: int = 100) -> List[Dict]:
        """Get all candidates from Firestore only."""
        if not self.db or not self.firebase_initialized:
            print("❌ Firestore not available")
            return []
    
        try:
            candidates_ref = self.db.collection(self.collection_name).limit(limit)
            docs = candidates_ref.stream()
            candidates = [doc.to_dict() for doc in docs]
            print(f"📋 Retrieved {len(candidates)} candidates from Firestore")
            return candidates
        except Exception as e:
            print(f"❌ Firestore get_all error: {e}")
            return []
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information."""
        debug_info = {
            'firebase_initialized': self.firebase_initialized,
            'firestore_client_exists': self.db is not None,
            'collection_name': self.collection_name,
            'firebase_apps_count': len(firebase_admin._apps),
            'storage_mode': 'firestore_only',
            'environment_variables_status': {
                'FIREBASE_PROJECT_ID': bool(os.getenv('FIREBASE_PROJECT_ID')),
                'FIREBASE_CLIENT_EMAIL': bool(os.getenv('FIREBASE_CLIENT_EMAIL')),
                'FIREBASE_PRIVATE_KEY': bool(os.getenv('FIREBASE_PRIVATE_KEY')),
                'FIREBASE_TYPE': bool(os.getenv('FIREBASE_TYPE')),
            }
        }
        
        # Try to get Firestore info
        if self.db:
            try:
                # Try a simple operation
                collections = list(self.db.collections())
                debug_info['firestore_collections'] = [col.id for col in collections]
                debug_info['firestore_accessible'] = True
            
                # Get candidate count
                candidates_ref = self.db.collection(self.collection_name)
                docs = list(candidates_ref.stream())
                debug_info['total_candidates'] = len(docs)
            except Exception as e:
                debug_info['firestore_error'] = str(e)
                debug_info['firestore_accessible'] = False
    
        return debug_info
    
    def update_candidate(self, session_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update candidate data in Firestore only."""
        if not self.db or not self.firebase_initialized:
            return False, "Firestore not available"
    
        try:
            updates['updated_at'] = datetime.now().isoformat()
        
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update(updates)
            print(f"✅ Updated in Firestore: {session_id}")
            return True, "Candidate updated successfully"
        
        except Exception as e:
            error_msg = f"Update error: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def delete_candidate(self, session_id: str) -> Tuple[bool, str]:
        """Delete candidate from Firestore only."""
        if not self.db or not self.firebase_initialized:
            return False, "Firestore not available"
    
        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
        
            # Check if document exists before deleting
            if not doc_ref.get().exists:
                return False, "Candidate not found"
        
            doc_ref.delete()
            print(f"🗑️ Deleted from Firestore: {session_id}")
            return True, "Candidate deleted successfully"
        
        except Exception as e:
            error_msg = f"Delete error: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def _load_candidates(self) -> List[Dict]:
        """Load all candidates from local storage."""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def validate_field(self, field_name: str, value: Any) -> Tuple[bool, str]:
        """Validate individual field."""
        try:
            if field_name == 'email':
                if not validators.email(value):
                    return False, "Please provide a valid email address."
                    
            elif field_name == 'phone':
                phone_digits = re.sub(r'\D', '', str(value))
                if len(phone_digits) < 10:
                    return False, "Please provide a valid phone number with at least 10 digits."
                    
            elif field_name == 'experience_years':
                try:
                    years = int(value)
                    if years < 0 or years > 50:
                        return False, "Experience years should be between 0 and 50."
                except ValueError:
                    return False, "Please provide experience as a number."
                    
            elif field_name == 'full_name':
                if len(str(value).strip()) < 2:
                    return False, "Please provide your full name."
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse_tech_stack(self, tech_input: str) -> Dict[str, List[str]]:
        """Parse tech stack input into categories."""
        tech_stack = {
            'Programming Languages': [],
            'Frameworks': [],
            'Databases': [],
            'Tools & Technologies': []
        }
        
        language_keywords = ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'typescript']
        framework_keywords = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'laravel', 'rails', 'nextjs', 'svelte']
        database_keywords = ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'cassandra', 'elasticsearch']
        tool_keywords = ['docker', 'kubernetes', 'aws', 'gcp', 'azure', 'git', 'jenkins', 'terraform', 'ansible']
        
        technologies = [tech.strip().lower() for tech in re.split(r'[,\n]', tech_input) if tech.strip()]
        
        for tech in technologies:
            categorized = False
            
            if any(lang in tech for lang in language_keywords):
                tech_stack['Programming Languages'].append(tech.title())
                categorized = True
            elif any(fw in tech for fw in framework_keywords):
                tech_stack['Frameworks'].append(tech.title())
                categorized = True
            elif any(db in tech for db in database_keywords):
                tech_stack['Databases'].append(tech.title())
                categorized = True
            elif any(tool in tech for tool in tool_keywords):
                tech_stack['Tools & Technologies'].append(tech.title())
                categorized = True
            
            if not categorized:
                tech_stack['Tools & Technologies'].append(tech.title())
        
        return {k: v for k, v in tech_stack.items() if v}
    
    def get_completion_percentage(self, candidate_data: Dict) -> float:
        """Calculate completion percentage of candidate data."""
        required_fields = ['full_name', 'email', 'phone', 'experience_years', 'desired_positions', 'location']
        completed = sum(1 for field in required_fields if candidate_data.get(field))
        return (completed / len(required_fields)) * 100
    
    def sanitize_data(self, data: Dict) -> Dict:
        """Sanitize sensitive data for logging/display."""
        sanitized = data.copy()
        
        if 'email' in sanitized and sanitized['email']:
            email_parts = sanitized['email'].split('@')
            if len(email_parts) == 2:
                sanitized['email'] = f"{email_parts[0][:2]}***@{email_parts[1]}"
        
        if 'phone' in sanitized and sanitized['phone']:
            phone = str(sanitized['phone'])
            sanitized['phone'] = f"***-***-{phone[-4:]}" if len(phone) >= 4 else "***"
        
        return sanitized
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics from Firestore only."""
        stats = {
            'firestore_connected': self.db is not None and self.firebase_initialized,
            'storage_mode': 'firestore_only',
            'total_candidates': 0,
            'recent_candidates': 0
        }
    
        if not self.db or not self.firebase_initialized:
            return stats
    
        try:
            candidates_ref = self.db.collection(self.collection_name)
            docs = list(candidates_ref.stream())
            stats['total_candidates'] = len(docs)
        
            # Count recent candidates (last 7 days)
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_query = candidates_ref.where('created_at', '>=', week_ago)
            recent_docs = list(recent_query.stream())
            stats['recent_candidates'] = len(recent_docs)
        
        except Exception as e:
            print(f"Error getting stats: {e}")
            stats['error'] = str(e)
    
        return stats