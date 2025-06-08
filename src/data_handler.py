"""Enhanced data handling with better debugging and error handling."""

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
    
    def __init__(self, firebase_config_path: str = None, storage_file: str = "data/candidates.json"):
        self.storage_file = storage_file
        self.db = None
        self.collection_name = "candidates"
        self.firebase_initialized = False
        
        # Initialize Firebase/Firestore
        self._initialize_firebase(firebase_config_path)
        self._ensure_data_directory()
    
    def _initialize_firebase(self, firebase_config_path: str):
        """Initialize Firebase with enhanced debugging."""
        print(f"🔍 Initializing Firebase...")
        print(f"📍 Config path: {firebase_config_path}")
        print(f"📁 Config exists: {os.path.exists(firebase_config_path) if firebase_config_path else False}")
        
        if not firebase_config_path:
            print("❌ No Firebase config path provided")
            return
            
        if not os.path.exists(firebase_config_path):
            print(f"❌ Firebase config file not found at: {firebase_config_path}")
            return
            
        try:
            # Check if Firebase app is already initialized
            print(f"🔍 Current Firebase apps: {len(firebase_admin._apps)}")
            
            if not firebase_admin._apps:
                print("🚀 Initializing new Firebase app...")
                cred = credentials.Certificate(firebase_config_path)
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
                'message': 'Connection test successful'
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
    
    def _ensure_data_directory(self):
        """Ensure data directory exists for local backup."""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump([], f)
    

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
        try:
            new_name = self._normalize_name(candidate_data.get('full_name', ''))
            new_email = candidate_data.get('email', '').lower().strip()
            new_phone = self._normalize_phone(candidate_data.get('phone', ''))
            
            # Check Firestore first
            if self.db:
                try:
                    candidates_ref = self.db.collection(self.collection_name)
                    
                    # Check email duplicates
                    if new_email:
                        email_query = candidates_ref.where('email', '==', new_email).limit(1)
                        email_docs = list(email_query.stream())
                        if email_docs:
                            return True, f"Email {new_email} already registered"
                    
                    # Check phone duplicates
                    if new_phone:
                        # Note: Firestore queries work best with exact matches
                        # For phone number variations, we'll check all candidates
                        all_candidates = candidates_ref.stream()
                        for doc in all_candidates:
                            existing = doc.to_dict()
                            existing_phone = self._normalize_phone(existing.get('phone', ''))
                            if existing_phone and existing_phone == new_phone:
                                return True, f"Phone number already registered"
                    
                    # Check name similarity (requires checking all candidates)
                    if new_name:
                        all_candidates = candidates_ref.stream()
                        for doc in all_candidates:
                            existing = doc.to_dict()
                            existing_name = self._normalize_name(existing.get('full_name', ''))
                            if existing_name and self._similarity_score(new_name, existing_name) > 0.85:
                                return True, f"Similar name already exists: {existing.get('full_name')}"
                
                except Exception as e:
                    print(f"Firestore duplicate check error: {e}")
                    # Fall through to local check
            
            # Fallback to local file check
            candidates = self._load_candidates()
            for existing in candidates:
                # Email check
                if new_email and existing.get('email', '').lower().strip() == new_email:
                    return True, f"Email {new_email} already registered"
                
                # Phone check
                existing_phone = self._normalize_phone(existing.get('phone', ''))
                if new_phone and existing_phone == new_phone:
                    return True, f"Phone number already registered"
                
                # Name similarity check
                existing_name = self._normalize_name(existing.get('full_name', ''))
                if new_name and self._similarity_score(new_name, existing_name) > 0.85:
                    return True, f"Similar name already exists: {existing.get('full_name')}"
            
            return False, ""
            
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return False, ""

    
    def save_candidate(self, candidate_data: Dict[str, Any], session_id: str) -> Tuple[bool, str]:
        """Enhanced save method with detailed debugging."""
        print(f"\n🚀 Starting candidate save process...")
        print(f"📋 Session ID: {session_id}")
        print(f"📊 Candidate data keys: {list(candidate_data.keys())}")
        print(f"🔥 Firestore initialized: {self.firebase_initialized}")
        print(f"🔗 Firestore client exists: {self.db is not None}")
        
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
            print(f"📊 Final data structure: {json.dumps(candidate_dict, indent=2, default=str)[:500]}...")
            
            # Save to Firestore
            firestore_success = False
            if self.db and self.firebase_initialized:
                try:
                    print(f"🔥 Attempting Firestore save to collection: {self.collection_name}")
                    print(f"📄 Document ID: {session_id}")
                    
                    # Use session_id as document ID for easy retrieval
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
                        firestore_success = True
                    else:
                        print("❌ Document verification failed - not found after write")
                        
                except Exception as e:
                    print(f"❌ Firestore save error: {type(e).__name__}: {e}")
                    print(f"📊 Error details: {str(e)}")
                    if hasattr(e, 'code'):
                        print(f"🔢 Error code: {e.code}")
            else:
                print("⚠️ Skipping Firestore save - not initialized")
            
            # Save to local file as backup
            local_success = False
            try:
                print("💾 Attempting local file save...")
                candidates = self._load_candidates()
                print(f"📊 Existing candidates count: {len(candidates)}")
                
                # Remove any existing entry with same session_id
                original_count = len(candidates)
                candidates = [c for c in candidates if c.get('session_id') != session_id]
                removed_count = original_count - len(candidates)
                if removed_count > 0:
                    print(f"🗑️ Removed {removed_count} existing entries with session_id: {session_id}")
                
                candidates.append(candidate_dict)
                print(f"📊 Total candidates after addition: {len(candidates)}")
                
                with open(self.storage_file, 'w') as f:
                    json.dump(candidates, f, indent=2, default=str)
                
                local_success = True
                print(f"✅ Local save successful to: {self.storage_file}")
                
            except Exception as e:
                print(f"❌ Local save error: {type(e).__name__}: {e}")
            
            # Return success if either storage method worked
            if firestore_success or local_success:
                storage_info = []
                if firestore_success:
                    storage_info.append("Firestore")
                if local_success:
                    storage_info.append("local backup")
                
                success_msg = f"Candidate saved successfully to {' and '.join(storage_info)}"
                print(f"🎉 {success_msg}")
                return True, success_msg
            else:
                error_msg = "Failed to save candidate data to any storage"
                print(f"❌ {error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Error saving candidate: {type(e).__name__}: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg


    def get_candidate_by_session(self, session_id: str) -> Optional[Dict]:
        """Get candidate data by session ID from Firestore or local storage."""
        # Try Firestore first
        if self.db:
            try:
                doc_ref = self.db.collection(self.collection_name).document(session_id)
                doc = doc_ref.get()
                if doc.exists:
                    print(f"📖 Retrieved from Firestore: {session_id}")
                    return doc.to_dict()
            except Exception as e:
                print(f"Firestore get error: {e}")
        
        # Fallback to local storage
        candidates = self._load_candidates()
        for candidate in candidates:
            if candidate.get('session_id') == session_id:
                print(f"📖 Retrieved from local storage: {session_id}")
                return candidate
        
        print(f"❌ Candidate not found: {session_id}")
        return None


    def get_all_candidates(self, limit: int = 100) -> List[Dict]:
        """Get all candidates from Firestore with local fallback."""
        candidates = []
        
        # Try Firestore first
        if self.db:
            try:
                candidates_ref = self.db.collection(self.collection_name).limit(limit)
                docs = candidates_ref.stream()
                candidates = [doc.to_dict() for doc in docs]
                print(f"📋 Retrieved {len(candidates)} candidates from Firestore")
                return candidates
            except Exception as e:
                print(f"Firestore get_all error: {e}")
        
        # Fallback to local storage
        candidates = self._load_candidates()
        print(f"📋 Retrieved {len(candidates)} candidates from local storage")
        return candidates[:limit]


    
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information."""
        debug_info = {
            'firebase_initialized': self.firebase_initialized,
            'firestore_client_exists': self.db is not None,
            'collection_name': self.collection_name,
            'storage_file': self.storage_file,
            'storage_file_exists': os.path.exists(self.storage_file),
            'firebase_apps_count': len(firebase_admin._apps),
        }
        
        # Try to get Firestore info
        if self.db:
            try:
                # Try a simple operation
                collections = list(self.db.collections())
                debug_info['firestore_collections'] = [col.id for col in collections]
                debug_info['firestore_accessible'] = True
            except Exception as e:
                debug_info['firestore_error'] = str(e)
                debug_info['firestore_accessible'] = False
        
        # Get local storage info
        try:
            candidates = self._load_candidates()
            debug_info['local_candidates_count'] = len(candidates)
        except Exception as e:
            debug_info['local_storage_error'] = str(e)
        
        return debug_info
    
    def update_candidate(self, session_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update candidate data in Firestore."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            # Update in Firestore
            firestore_success = False
            if self.db:
                try:
                    doc_ref = self.db.collection(self.collection_name).document(session_id)
                    doc_ref.update(updates)
                    firestore_success = True
                    print(f"✅ Updated in Firestore: {session_id}")
                except Exception as e:
                    print(f"❌ Firestore update error: {e}")
            
            # Update in local storage
            local_success = False
            try:
                candidates = self._load_candidates()
                for i, candidate in enumerate(candidates):
                    if candidate.get('session_id') == session_id:
                        candidates[i].update(updates)
                        local_success = True
                        break
                
                if local_success:
                    with open(self.storage_file, 'w') as f:
                        json.dump(candidates, f, indent=2, default=str)
                    print(f"💾 Updated in local storage: {session_id}")
            except Exception as e:
                print(f"❌ Local update error: {e}")
            
            if firestore_success or local_success:
                return True, "Candidate updated successfully"
            else:
                return False, "Failed to update candidate"
                
        except Exception as e:
            return False, f"Update error: {e}"
    
    def delete_candidate(self, session_id: str) -> Tuple[bool, str]:
        """Delete candidate from Firestore and local storage."""
        try:
            # Delete from Firestore
            firestore_success = False
            if self.db:
                try:
                    doc_ref = self.db.collection(self.collection_name).document(session_id)
                    doc_ref.delete()
                    firestore_success = True
                    print(f"🗑️ Deleted from Firestore: {session_id}")
                except Exception as e:
                    print(f"❌ Firestore delete error: {e}")
            
            # Delete from local storage
            local_success = False
            try:
                candidates = self._load_candidates()
                original_count = len(candidates)
                candidates = [c for c in candidates if c.get('session_id') != session_id]
                
                if len(candidates) < original_count:
                    with open(self.storage_file, 'w') as f:
                        json.dump(candidates, f, indent=2, default=str)
                    local_success = True
                    print(f"🗑️ Deleted from local storage: {session_id}")
            except Exception as e:
                print(f"❌ Local delete error: {e}")
            
            if firestore_success or local_success:
                return True, "Candidate deleted successfully"
            else:
                return False, "Candidate not found"
                
        except Exception as e:
            return False, f"Delete error: {e}"
    
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
        """Get database statistics."""
        stats = {
            'firestore_connected': self.db is not None,
            'local_storage_path': self.storage_file,
            'total_candidates': 0,
            'recent_candidates': 0
        }
        
        try:
            # Count from Firestore if available
            if self.db:
                candidates_ref = self.db.collection(self.collection_name)
                docs = list(candidates_ref.stream())
                stats['total_candidates'] = len(docs)
                
                # Count recent candidates (last 7 days)
                from datetime import datetime, timedelta
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                recent_query = candidates_ref.where('created_at', '>=', week_ago)
                recent_docs = list(recent_query.stream())
                stats['recent_candidates'] = len(recent_docs)
            else:
                # Fallback to local count
                candidates = self._load_candidates()
                stats['total_candidates'] = len(candidates)
                
        except Exception as e:
            print(f"Error getting stats: {e}")
        
        return stats