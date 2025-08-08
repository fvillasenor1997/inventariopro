
import os
import logging

class AndroidUtils:
    def __init__(self):
        self.is_android = self._detect_android()
        
    def _detect_android(self):
        """Detect if running on Android"""
        try:
            import jnius
            return True
        except ImportError:
            return False
    
    def get_data_directory(self):
        """Get application data directory"""
        try:
            if self.is_android:
                from android.storage import primary_external_storage_path
                return os.path.join(primary_external_storage_path(), 'InventarioApp')
            else:
                # Desktop/server environment
                home_dir = os.path.expanduser('~')
                data_dir = os.path.join(home_dir, '.inventario_app')
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
        except Exception as e:
            logging.warning(f"Error getting data directory: {e}")
            # Fallback to current directory
            fallback_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    
    def request_storage_permissions(self):
        """Request storage permissions on Android"""
        try:
            if self.is_android:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
                logging.info("Storage permissions requested")
        except ImportError:
            logging.info("Not on Android, permissions not needed")
        except Exception as e:
            logging.warning(f"Error requesting permissions: {e}")
