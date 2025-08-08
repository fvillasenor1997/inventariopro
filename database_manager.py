
import sqlite3
import os
import logging
import json
import uuid
from datetime import datetime
from android_utils import AndroidUtils

class DatabaseManager:
    def __init__(self):
        self.android_utils = AndroidUtils()
        self.db_path = os.path.join(self.android_utils.get_data_directory(), 'inventory.db')
        self.init_database()
        logging.info(f"Database initialized at: {self.db_path}")

    def init_database(self):
        """Initialize database and create tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create inventory table with sync support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras TEXT NOT NULL,
                    descripcion TEXT,
                    cantidad INTEGER NOT NULL,
                    auditor TEXT,
                    locacion TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    local_id TEXT UNIQUE,
                    firebase_id TEXT,
                    sync_status INTEGER DEFAULT 0,
                    created_by TEXT,
                    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_status ON inventory(sync_status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_local_id ON inventory(local_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_firebase_id ON inventory(firebase_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON inventory(timestamp)')

            # Create users table for local authentication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')

            # Create audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    user_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logging.info("Database tables created successfully")

        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise

    def add_record_with_sync(self, codigo_barras, descripcion, cantidad, auditor, locacion, created_by):
        """Add inventory record with sync support"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            local_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO inventory 
                (codigo_barras, descripcion, cantidad, auditor, locacion, local_id, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_barras, descripcion, cantidad, auditor, locacion, local_id, created_by))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Record added with local_id: {local_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding record: {e}")
            return False

    def get_last_records_with_sync_status(self, limit=50):
        """Get last records with sync status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codigo_barras, descripcion, cantidad, auditor, locacion, sync_status
                FROM inventory 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            records = cursor.fetchall()
            conn.close()
            
            return records
            
        except Exception as e:
            logging.error(f"Error getting records: {e}")
            return []

    def get_pending_sync_count(self):
        """Get count of pending sync records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM inventory WHERE sync_status = 0')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logging.error(f"Error getting pending sync count: {e}")
            return 0

    def sync_pending_records(self, firebase_manager):
        """Sync pending records with Firebase"""
        try:
            if not firebase_manager:
                return 0
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get pending records
            cursor.execute('''
                SELECT id, codigo_barras, descripcion, cantidad, auditor, locacion, 
                       timestamp, local_id, created_by
                FROM inventory 
                WHERE sync_status = 0
                LIMIT 10
            ''')
            
            pending_records = cursor.fetchall()
            success_count = 0
            
            for record in pending_records:
                record_data = {
                    'codigo_barras': record[1],
                    'descripcion': record[2],
                    'cantidad': record[3],
                    'auditor': record[4],
                    'locacion': record[5],
                    'timestamp': record[6],
                    'local_id': record[7],
                    'created_by': record[8]
                }
                
                success, message = firebase_manager.sync_record(record_data)
                
                if success:
                    # Mark as synced
                    cursor.execute('''
                        UPDATE inventory 
                        SET sync_status = 1, last_modified = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (record[0],))
                    success_count += 1
            
            conn.commit()
            conn.close()
            
            return success_count
            
        except Exception as e:
            logging.error(f"Error syncing pending records: {e}")
            return 0

    def update_record(self, record_id, codigo_barras, descripcion, cantidad, auditor, locacion):
        """Update inventory record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE inventory 
                SET codigo_barras = ?, descripcion = ?, cantidad = ?, 
                    auditor = ?, locacion = ?, last_modified = CURRENT_TIMESTAMP,
                    sync_status = 0
                WHERE id = ?
            ''', (codigo_barras, descripcion, cantidad, auditor, locacion, record_id))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Record updated: {record_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating record: {e}")
            return False

    def delete_record(self, record_id):
        """Delete inventory record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM inventory WHERE id = ?', (record_id,))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Record deleted: {record_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting record: {e}")
            return False

    def get_record_by_id(self, record_id):
        """Get record by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codigo_barras, descripcion, cantidad, auditor, locacion
                FROM inventory WHERE id = ?
            ''', (record_id,))
            
            record = cursor.fetchone()
            conn.close()
            
            return record
            
        except Exception as e:
            logging.error(f"Error getting record by ID: {e}")
            return None

    def search_records(self, search_text):
        """Search records by text"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_pattern = f'%{search_text}%'
            
            cursor.execute('''
                SELECT id, codigo_barras, descripcion, cantidad, auditor, locacion, sync_status
                FROM inventory 
                WHERE codigo_barras LIKE ? OR descripcion LIKE ? 
                   OR auditor LIKE ? OR locacion LIKE ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (search_pattern, search_pattern, search_pattern, search_pattern))
            
            records = cursor.fetchall()
            conn.close()
            
            return records
            
        except Exception as e:
            logging.error(f"Error searching records: {e}")
            return []

    def get_last_values(self):
        """Get last used values for UI"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT auditor, locacion
                FROM inventory 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'auditor': result[0],
                    'locacion': result[1]
                }
            return {}
            
        except Exception as e:
            logging.error(f"Error getting last values: {e}")
            return {}

    def get_statistics(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total records
            cursor.execute('SELECT COUNT(*) FROM inventory')
            total_records = cursor.fetchone()[0]
            
            # Total quantity
            cursor.execute('SELECT SUM(cantidad) FROM inventory')
            total_quantity = cursor.fetchone()[0] or 0
            
            # Unique products
            cursor.execute('SELECT COUNT(DISTINCT codigo_barras) FROM inventory')
            unique_products = cursor.fetchone()[0]
            
            # Last record date
            cursor.execute('SELECT MAX(timestamp) FROM inventory')
            last_record_date = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_records': total_records,
                'total_quantity': total_quantity,
                'unique_products': unique_products,
                'last_record_date': last_record_date
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}

    def get_last_records(self, limit=10):
        """Get last records for CLI display"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT codigo_barras, descripcion, cantidad, auditor, locacion, timestamp, sync_status
                FROM inventory 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            records = cursor.fetchall()
            conn.close()
            
            return records
            
        except Exception as e:
            logging.error(f"Error getting last records: {e}")
            return []
