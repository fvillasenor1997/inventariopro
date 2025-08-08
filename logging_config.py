
import logging
import os
from datetime import datetime

class AndroidUtils:
    def get_data_directory(self):
        """Get data directory for the application"""
        try:
            # For desktop/server environments
            data_dir = os.path.join(os.path.expanduser('~'), '.inventario_app')
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception as e:
            # Fallback to current directory
            return os.getcwd()

def setup_logging():
    """Setup logging configuration"""
    try:
        # Create logs directory if it doesn't exist
        android_utils = AndroidUtils()
        data_dir = android_utils.get_data_directory()
        logs_dir = os.path.join(data_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(logs_dir, f'inventory_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logging.info("Logging configurado correctamente")
        
    except Exception as e:
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.warning(f"Error configurando logging avanzado: {e}")
