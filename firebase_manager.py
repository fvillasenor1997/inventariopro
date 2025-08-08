
import json
import logging
import requests
import time
from datetime import datetime
from threading import Lock

class FirebaseManager:
    def __init__(self, config):
        """Initialize Firebase manager with configuration"""
        self.config = config
        self.project_id = config.get('projectId')
        self.api_key = config.get('apiKey')
        self.auth_domain = config.get('authDomain')
        self.database_url = config.get('databaseURL')
        self.storage_bucket = config.get('storageBucket')
        
        self.auth_token = None
        self.user_id = None
        self.last_sync = None
        self._sync_lock = Lock()
        
        logging.info(f"Firebase manager initialized for project: {self.project_id}")

    def is_online(self):
        """Check if Firebase is accessible"""
        try:
            response = requests.get(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}", timeout=5)
            return response.status_code in [400, 200]  # 400 is expected for GET without data
        except:
            return False

    def authenticate_user(self, username, password):
        """Authenticate user with Firebase Auth"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            
            # For simplicity, we'll use email format for username
            email = username if '@' in username else f"{username}@inventario.app"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('idToken')
                self.user_id = data.get('localId')
                logging.info(f"User authenticated successfully: {username}")
                return True, "Authentication successful"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Authentication failed')
                logging.warning(f"Authentication failed: {error_message}")
                return False, error_message
                
        except requests.RequestException as e:
            logging.error(f"Network error during authentication: {e}")
            return False, "Network error"
        except Exception as e:
            logging.error(f"Error during authentication: {e}")
            return False, str(e)

    def create_user(self, username, password):
        """Create new user in Firebase Auth"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            
            email = username if '@' in username else f"{username}@inventario.app"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('idToken')
                self.user_id = data.get('localId')
                logging.info(f"User created successfully: {username}")
                return True, "User created successfully"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'User creation failed')
                logging.warning(f"User creation failed: {error_message}")
                return False, error_message
                
        except requests.RequestException as e:
            logging.error(f"Network error during user creation: {e}")
            return False, "Network error"
        except Exception as e:
            logging.error(f"Error during user creation: {e}")
            return False, str(e)

    def sync_record(self, record_data):
        """Sync individual record to Firestore"""
        try:
            if not self.auth_token:
                return False, "Not authenticated"

            with self._sync_lock:
                # Prepare Firestore document
                firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/inventory"
                
                headers = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
                
                # Convert record to Firestore format
                document = {
                    "fields": {
                        "codigo_barras": {"stringValue": str(record_data.get('codigo_barras', ''))},
                        "descripcion": {"stringValue": str(record_data.get('descripcion', ''))},
                        "cantidad": {"integerValue": str(record_data.get('cantidad', 0))},
                        "auditor": {"stringValue": str(record_data.get('auditor', ''))},
                        "locacion": {"stringValue": str(record_data.get('locacion', ''))},
                        "timestamp": {"timestampValue": record_data.get('timestamp', datetime.now().isoformat() + 'Z')},
                        "user_id": {"stringValue": str(self.user_id)},
                        "local_id": {"stringValue": str(record_data.get('local_id', ''))},
                        "sync_status": {"booleanValue": True}
                    }
                }
                
                response = requests.post(firestore_url, json=document, headers=headers, timeout=15)
                
                if response.status_code in [200, 201]:
                    logging.info(f"Record synced successfully: {record_data.get('codigo_barras')}")
                    return True, "Record synced successfully"
                else:
                    error_msg = f"Sync failed with status {response.status_code}"
                    logging.warning(error_msg)
                    return False, error_msg
                    
        except requests.RequestException as e:
            logging.error(f"Network error during sync: {e}")
            return False, "Network error"
        except Exception as e:
            logging.error(f"Error syncing record: {e}")
            return False, str(e)

    def sync_multiple_records(self, records):
        """Sync multiple records to Firebase"""
        try:
            if not self.auth_token:
                return 0

            success_count = 0
            
            for record in records:
                success, message = self.sync_record(record)
                if success:
                    success_count += 1
                else:
                    logging.warning(f"Failed to sync record {record.get('local_id')}: {message}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            logging.info(f"Synced {success_count} of {len(records)} records")
            return success_count
            
        except Exception as e:
            logging.error(f"Error syncing multiple records: {e}")
            return 0

    def fetch_updates(self, last_sync_timestamp=None):
        """Fetch updates from Firebase since last sync"""
        try:
            if not self.auth_token:
                return []

            firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/inventory"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Add timestamp filter if provided
            params = {}
            if last_sync_timestamp:
                params['orderBy'] = 'timestamp'
                params['where'] = f'timestamp > {last_sync_timestamp}'
            
            response = requests.get(firestore_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                updates = []
                for doc in documents:
                    fields = doc.get('fields', {})
                    update = {
                        'firebase_id': doc.get('name', '').split('/')[-1],
                        'codigo_barras': fields.get('codigo_barras', {}).get('stringValue', ''),
                        'descripcion': fields.get('descripcion', {}).get('stringValue', ''),
                        'cantidad': int(fields.get('cantidad', {}).get('integerValue', 0)),
                        'auditor': fields.get('auditor', {}).get('stringValue', ''),
                        'locacion': fields.get('locacion', {}).get('stringValue', ''),
                        'timestamp': fields.get('timestamp', {}).get('timestampValue', ''),
                        'user_id': fields.get('user_id', {}).get('stringValue', ''),
                        'local_id': fields.get('local_id', {}).get('stringValue', '')
                    }
                    updates.append(update)
                
                logging.info(f"Fetched {len(updates)} updates from Firebase")
                return updates
            else:
                logging.warning(f"Failed to fetch updates: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logging.error(f"Network error fetching updates: {e}")
            return []
        except Exception as e:
            logging.error(f"Error fetching updates: {e}")
            return []

    def get_audit_trail(self, user_id=None, start_date=None, end_date=None):
        """Get audit trail of inventory operations"""
        try:
            if not self.auth_token:
                return []

            firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/inventory"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Build query parameters
            params = {'orderBy': 'timestamp desc'}
            
            # Add filters if provided
            filters = []
            if user_id:
                filters.append(f'user_id = "{user_id}"')
            if start_date:
                filters.append(f'timestamp >= "{start_date}"')
            if end_date:
                filters.append(f'timestamp <= "{end_date}"')
            
            if filters:
                params['where'] = ' AND '.join(filters)
            
            response = requests.get(firestore_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                audit_records = []
                for doc in documents:
                    fields = doc.get('fields', {})
                    record = {
                        'firebase_id': doc.get('name', '').split('/')[-1],
                        'codigo_barras': fields.get('codigo_barras', {}).get('stringValue', ''),
                        'descripcion': fields.get('descripcion', {}).get('stringValue', ''),
                        'cantidad': int(fields.get('cantidad', {}).get('integerValue', 0)),
                        'auditor': fields.get('auditor', {}).get('stringValue', ''),
                        'locacion': fields.get('locacion', {}).get('stringValue', ''),
                        'timestamp': fields.get('timestamp', {}).get('timestampValue', ''),
                        'user_id': fields.get('user_id', {}).get('stringValue', '')
                    }
                    audit_records.append(record)
                
                logging.info(f"Retrieved {len(audit_records)} audit records")
                return audit_records
            else:
                logging.warning(f"Failed to get audit trail: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logging.error(f"Network error getting audit trail: {e}")
            return []
        except Exception as e:
            logging.error(f"Error getting audit trail: {e}")
            return []

    def refresh_auth_token(self):
        """Refresh authentication token if needed"""
        try:
            # This would typically use a refresh token
            # For simplicity, we'll assume the token is valid for the session
            logging.info("Auth token refresh not implemented - using session token")
            return True
        except Exception as e:
            logging.error(f"Error refreshing auth token: {e}")
            return False

    def get_server_timestamp(self):
        """Get server timestamp for synchronization"""
        try:
            # Return current ISO timestamp
            return datetime.now().isoformat() + 'Z'
        except Exception as e:
            logging.error(f"Error getting server timestamp: {e}")
            return None

    def validate_connection(self):
        """Validate Firebase connection and authentication"""
        try:
            if not self.auth_token:
                return False, "Not authenticated"
            
            # Test connection with a simple query
            firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/inventory"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            params = {'pageSize': 1}
            
            response = requests.get(firestore_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return True, "Connection validated"
            elif response.status_code == 401:
                return False, "Authentication expired"
            else:
                return False, f"Connection failed: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
