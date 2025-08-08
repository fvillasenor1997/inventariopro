
import os
import json
import logging
from android_utils import AndroidUtils

class FileManager:
    def __init__(self):
        self.android_utils = AndroidUtils()
        
    def get_master_file_path(self):
        """Get path for master file"""
        data_dir = self.android_utils.get_data_directory()
        return os.path.join(data_dir, 'master_items.json')
    
    def load_excel_file(self, file_path):
        """Load Excel file and return dictionary"""
        try:
            # Check if openpyxl is available
            try:
                import openpyxl
            except ImportError:
                return False, "openpyxl no está disponible. Instale con: pip install openpyxl"
            
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            # Load Excel file
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active
            
            master_dict = {}
            
            # Read data from sheet (assuming columns A=codigo, B=descripcion)
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header
                if row[0] is not None and row[1] is not None:
                    codigo = str(row[0]).strip()
                    descripcion = str(row[1]).strip()
                    if codigo and descripcion:
                        master_dict[codigo] = descripcion
            
            logging.info(f"Loaded {len(master_dict)} items from Excel file")
            return True, master_dict
            
        except Exception as e:
            logging.error(f"Error loading Excel file: {e}")
            return False, str(e)
    
    def export_to_json(self, data, filename):
        """Export data to JSON file"""
        try:
            data_dir = self.android_utils.get_data_directory()
            file_path = os.path.join(data_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logging.info(f"Data exported to {file_path}")
            return True, file_path
            
        except Exception as e:
            logging.error(f"Error exporting to JSON: {e}")
            return False, str(e)
    
    def import_from_json(self, file_path):
        """Import data from JSON file"""
        try:
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logging.info(f"Data imported from {file_path}")
            return True, data
            
        except Exception as e:
            logging.error(f"Error importing from JSON: {e}")
            return False, str(e)
