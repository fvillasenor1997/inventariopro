
import json
import os
import sqlite3
import datetime
import logging
import math
from urllib.parse import quote
import webbrowser
from collections import Counter
from threading import Thread
import traceback
import hashlib
import time

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    import requests
    HAS_FIREBASE = True
    logging.info("Firebase disponible")
except ImportError:
    HAS_FIREBASE = False
    logging.warning("Firebase no disponible")

# Import our custom modules
from logging_config import setup_logging
from android_utils import AndroidUtils
from database_manager import DatabaseManager
from file_manager import FileManager
from firebase_manager import FirebaseManager

# Setup logging first
setup_logging()

# --- Helper Function ---
def truncate_text(text, max_length=15):
    """Trunca el texto a una longitud máxima, añadiendo '...' si es necesario."""
    text = str(text)
    if len(text) > max_length:
        return text[:max_length] + '...'
    return text

# --- Importaciones de Kivy (Interfaz Gráfica) ---
try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.popup import Popup
    from kivy.uix.filechooser import FileChooserListView
    from kivy.uix.spinner import Spinner
    from kivy.uix.widget import Widget
    from kivy.clock import Clock, mainthread
    from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty, DictProperty
    from kivy.metrics import dp
    from kivy.graphics import Color, Rectangle, Line
    
    # Importaciones para permisos de Android y plyer
    HAS_ANDROID_PERMISSIONS = False
    HAS_PLYER_FILECHOOSER = False
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import primary_external_storage_path
        HAS_ANDROID_PERMISSIONS = True
        logging.info("Módulos de permisos de Android disponibles")
    except ImportError:
        logging.info("Módulos de permisos de Android no disponibles (ejecutando en entorno no Android).")
    
    try:
        from plyer import filechooser
        HAS_PLYER_FILECHOOSER = True
        logging.info("plyer.filechooser disponible")
    except ImportError:
        logging.info("plyer.filechooser no disponible. Usando FileChooserListView de Kivy.")

except ImportError as e:
    print(f"Error importing Kivy: {e}")
    logging.error(f"Error importing Kivy: {e}")
    exit(1)

# Importación opcional de openpyxl
try:
    import openpyxl
    HAS_OPENPYXL = True
    logging.info("openpyxl disponible")
except ImportError:
    HAS_OPENPYXL = False
    logging.warning("openpyxl no está disponible. Funcionalidad de Excel deshabilitada.")

# --- 🎨 Paleta de Colores de Alto Contraste ---
APP_BG_COLOR = (0.94, 0.95, 0.96, 1)
CARD_BG_COLOR = (1, 1, 1, 1)
ALT_ROW_COLOR = (0.90, 0.91, 0.92, 1)
TEXT_COLOR = (0.1, 0.1, 0.1, 1)
WHITE_TEXT_COLOR = (1, 1, 1, 1)
POPUP_BG_COLOR = (0.2, 0.22, 0.25, 1)
TAB_ACTIVE_COLOR = (0.11, 0.46, 0.85, 1)
TAB_INACTIVE_COLOR = (0.75, 0.78, 0.8, 1)
SUCCESS_COLOR = (0.13, 0.59, 0.28, 1)
ERROR_COLOR = (0.86, 0.22, 0.2, 1)
ORANGE_COLOR = (0.9, 0.5, 0, 1)
BLUE_EXPORT_COLOR = (0.1, 0.5, 0.9, 1)

# Set window background color safely
try:
    if Window is not None:
        Window.clearcolor = APP_BG_COLOR
    else:
        logging.warning("Window is None, cannot set clearcolor")
except Exception as e:
    logging.error(f"Error setting window clearcolor: {e}")

# Initialize utility classes
android_utils = AndroidUtils()
file_manager = FileManager()

# --- Firebase Configuration Screen ---
class FirebaseConfigScreen(BoxLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20
        self.app_instance = app_instance
        self.build_ui()

    def build_ui(self):
        """Build Firebase configuration UI"""
        try:
            # Title
            title = Label(text='Configuración de Firebase', font_size='24sp', 
                         size_hint_y=None, height=dp(50), bold=True, color=TEXT_COLOR)
            self.add_widget(title)

            # Instructions
            instructions = Label(
                text='Ingrese los datos de configuración de Firebase.\nEstos datos se guardarán de forma segura para uso offline.',
                text_size=(None, None), halign='center', valign='middle',
                size_hint_y=None, height=dp(60), color=TEXT_COLOR
            )
            self.add_widget(instructions)

            # Form fields
            form_layout = GridLayout(cols=2, spacing=15, size_hint_y=None)
            form_layout.bind(minimum_height=form_layout.setter('height'))

            # Firebase Project ID
            form_layout.add_widget(Label(text='Project ID:', halign='right', color=TEXT_COLOR))
            self.project_id_input = TextInput(hint_text='tu-proyecto-firebase', multiline=False)
            form_layout.add_widget(self.project_id_input)

            # Firebase API Key
            form_layout.add_widget(Label(text='API Key:', halign='right', color=TEXT_COLOR))
            self.api_key_input = TextInput(hint_text='AIzaSy...', multiline=False, password=True)
            form_layout.add_widget(self.api_key_input)

            # Firebase Auth Domain
            form_layout.add_widget(Label(text='Auth Domain:', halign='right', color=TEXT_COLOR))
            self.auth_domain_input = TextInput(hint_text='tu-proyecto.firebaseapp.com', multiline=False)
            form_layout.add_widget(self.auth_domain_input)

            # Firebase Database URL
            form_layout.add_widget(Label(text='Database URL:', halign='right', color=TEXT_COLOR))
            self.database_url_input = TextInput(hint_text='https://tu-proyecto-default-rtdb.firebaseio.com/', multiline=False)
            form_layout.add_widget(self.database_url_input)

            # Storage Bucket
            form_layout.add_widget(Label(text='Storage Bucket:', halign='right', color=TEXT_COLOR))
            self.storage_bucket_input = TextInput(hint_text='tu-proyecto.appspot.com', multiline=False)
            form_layout.add_widget(self.storage_bucket_input)

            self.add_widget(form_layout)

            # Buttons
            button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=20)
            
            save_btn = Button(text='Guardar Configuración', color=WHITE_TEXT_COLOR, 
                             background_color=SUCCESS_COLOR)
            save_btn.bind(on_press=self.save_firebase_config)
            
            skip_btn = Button(text='Usar Solo Offline', color=WHITE_TEXT_COLOR, 
                             background_color=ORANGE_COLOR)
            skip_btn.bind(on_press=self.skip_firebase_config)

            button_layout.add_widget(save_btn)
            button_layout.add_widget(skip_btn)
            self.add_widget(button_layout)

            # Status label
            self.status_label = Label(text='', size_hint_y=None, height=dp(30), color=ERROR_COLOR)
            self.add_widget(self.status_label)

            # Load existing config if available
            self.load_existing_config()

        except Exception as e:
            logging.error(f"Error building Firebase config UI: {e}")

    def load_existing_config(self):
        """Load existing Firebase configuration"""
        try:
            config_file = os.path.join(android_utils.get_data_directory(), 'firebase_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.project_id_input.text = config.get('projectId', '')
                    self.api_key_input.text = config.get('apiKey', '')
                    self.auth_domain_input.text = config.get('authDomain', '')
                    self.database_url_input.text = config.get('databaseURL', '')
                    self.storage_bucket_input.text = config.get('storageBucket', '')
                    self.status_label.text = 'Configuración existente cargada'
                    self.status_label.color = SUCCESS_COLOR
        except Exception as e:
            logging.error(f"Error loading Firebase config: {e}")

    def save_firebase_config(self, instance):
        """Save Firebase configuration"""
        try:
            # Validate inputs
            if not all([
                self.project_id_input.text.strip(),
                self.api_key_input.text.strip(),
                self.auth_domain_input.text.strip()
            ]):
                self.status_label.text = 'Por favor complete todos los campos obligatorios'
                self.status_label.color = ERROR_COLOR
                return

            config = {
                'projectId': self.project_id_input.text.strip(),
                'apiKey': self.api_key_input.text.strip(),
                'authDomain': self.auth_domain_input.text.strip(),
                'databaseURL': self.database_url_input.text.strip(),
                'storageBucket': self.storage_bucket_input.text.strip()
            }

            # Save to file
            config_file = os.path.join(android_utils.get_data_directory(), 'firebase_config.json')
            with open(config_file, 'w') as f:
                json.dump(config, f)

            self.status_label.text = 'Configuración guardada correctamente'
            self.status_label.color = SUCCESS_COLOR

            # Initialize Firebase and proceed to login
            Clock.schedule_once(lambda dt: self.app_instance.initialize_firebase_and_login(), 2)

        except Exception as e:
            logging.error(f"Error saving Firebase config: {e}")
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = ERROR_COLOR

    def skip_firebase_config(self, instance):
        """Skip Firebase configuration and use offline only"""
        self.app_instance.firebase_enabled = False
        self.app_instance.show_login_screen()

# --- Login Screen ---
class LoginScreen(BoxLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 50
        self.spacing = 30
        self.app_instance = app_instance
        self.build_ui()

    def build_ui(self):
        """Build login UI"""
        try:
            # Title
            title = Label(text='Inventario App', font_size='32sp', 
                         size_hint_y=None, height=dp(80), bold=True, color=TEXT_COLOR)
            self.add_widget(title)

            # Connection status
            self.connection_status = Label(text='', size_hint_y=None, height=dp(30), color=ORANGE_COLOR)
            self.add_widget(self.connection_status)
            self.update_connection_status()

            # Login form
            form_layout = GridLayout(cols=2, spacing=20, size_hint_y=None, height=dp(120))
            
            form_layout.add_widget(Label(text='Usuario:', halign='right', color=TEXT_COLOR))
            self.username_input = TextInput(hint_text='Ingrese su usuario', multiline=False)
            form_layout.add_widget(self.username_input)

            form_layout.add_widget(Label(text='Contraseña:', halign='right', color=TEXT_COLOR))
            self.password_input = TextInput(hint_text='Ingrese su contraseña', multiline=False, password=True)
            self.password_input.bind(on_text_validate=self.login)
            form_layout.add_widget(self.password_input)

            self.add_widget(form_layout)

            # Login button
            login_btn = Button(text='Iniciar Sesión', size_hint_y=None, height=dp(50),
                              color=WHITE_TEXT_COLOR, background_color=TAB_ACTIVE_COLOR)
            login_btn.bind(on_press=self.login)
            self.add_widget(login_btn)

            # Status label
            self.status_label = Label(text='', size_hint_y=None, height=dp(30))
            self.add_widget(self.status_label)

            # Options
            options_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
            
            config_btn = Button(text='Configurar Firebase', size_hint_x=0.5,
                               color=WHITE_TEXT_COLOR, background_color=ORANGE_COLOR)
            config_btn.bind(on_press=self.show_firebase_config)
            
            offline_btn = Button(text='Modo Offline', size_hint_x=0.5,
                                color=TEXT_COLOR, background_color=ALT_ROW_COLOR)
            offline_btn.bind(on_press=self.login_offline)

            options_layout.add_widget(config_btn)
            options_layout.add_widget(offline_btn)
            self.add_widget(options_layout)

        except Exception as e:
            logging.error(f"Error building login UI: {e}")

    def update_connection_status(self):
        """Update connection status"""
        if self.app_instance.firebase_enabled and self.app_instance.firebase_manager:
            if self.app_instance.firebase_manager.is_online():
                self.connection_status.text = '🟢 Conectado - Firebase Online'
                self.connection_status.color = SUCCESS_COLOR
            else:
                self.connection_status.text = '🟡 Firebase configurado - Sin conexión'
                self.connection_status.color = ORANGE_COLOR
        else:
            self.connection_status.text = '🔴 Modo Offline - Firebase no configurado'
            self.connection_status.color = ERROR_COLOR

    def login(self, instance):
        """Handle login"""
        try:
            username = self.username_input.text.strip()
            password = self.password_input.text.strip()

            if not username or not password:
                self.status_label.text = 'Por favor ingrese usuario y contraseña'
                self.status_label.color = ERROR_COLOR
                return

            self.status_label.text = 'Iniciando sesión...'
            self.status_label.color = ORANGE_COLOR

            # Try Firebase authentication if available
            if self.app_instance.firebase_enabled and self.app_instance.firebase_manager:
                Thread(target=self._firebase_login, args=(username, password), daemon=True).start()
            else:
                # Local authentication
                self._local_login(username, password)

        except Exception as e:
            logging.error(f"Error in login: {e}")
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = ERROR_COLOR

    def _firebase_login(self, username, password):
        """Firebase authentication in background thread"""
        try:
            success, message = self.app_instance.firebase_manager.authenticate_user(username, password)
            
            def update_ui(dt):
                if success:
                    self.status_label.text = 'Login exitoso'
                    self.status_label.color = SUCCESS_COLOR
                    self.app_instance.current_user = username
                    self.app_instance.show_main_screen()
                else:
                    # Try local login as fallback
                    self._local_login(username, password)
            
            Clock.schedule_once(update_ui)
            
        except Exception as e:
            logging.error(f"Error in Firebase login: {e}")
            Clock.schedule_once(lambda dt: self._local_login(username, password))

    def _local_login(self, username, password):
        """Local authentication"""
        try:
            # Simple local authentication (you can enhance this)
            users_file = os.path.join(android_utils.get_data_directory(), 'users.json')
            
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    users = json.load(f)
            else:
                # Create default admin user
                users = {
                    'admin': hashlib.sha256('admin'.encode()).hexdigest()
                }
                with open(users_file, 'w') as f:
                    json.dump(users, f)

            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if username in users and users[username] == password_hash:
                self.status_label.text = 'Login exitoso (Offline)'
                self.status_label.color = SUCCESS_COLOR
                self.app_instance.current_user = username
                self.app_instance.show_main_screen()
            else:
                self.status_label.text = 'Usuario o contraseña incorrectos'
                self.status_label.color = ERROR_COLOR

        except Exception as e:
            logging.error(f"Error in local login: {e}")
            self.status_label.text = f'Error en login: {str(e)}'
            self.status_label.color = ERROR_COLOR

    def login_offline(self, instance):
        """Login in offline mode"""
        self.app_instance.firebase_enabled = False
        self.app_instance.current_user = 'offline_user'
        self.app_instance.show_main_screen()

    def show_firebase_config(self, instance):
        """Show Firebase configuration screen"""
        self.app_instance.show_firebase_config()

# --- Enhanced Inventory Screen with Firebase Sync ---
class InventoryScreen(BoxLayout):
    editing_id = None

    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        self.app_instance = app_instance
        self.db_manager = DatabaseManager()
        self.sync_status = 'offline'
        self.pending_sync_count = 0
        self.build_ui()
        Clock.schedule_once(self._delayed_init, 0.1)

    def _delayed_init(self, dt):
        """Initialize data after UI is built"""
        Thread(target=self._load_data_thread, daemon=True).start()
        # Start sync timer if Firebase is enabled
        if self.app_instance.firebase_enabled:
            Clock.schedule_interval(self._sync_with_firebase, 30)  # Sync every 30 seconds

    def _load_data_thread(self):
        """Load data in background thread"""
        try:
            logging.info("Iniciando carga de datos en hilo secundario")
            self._display_last_records()
            self._load_last_values_to_ui()
            self._update_pending_sync_count()
            logging.info("Carga de datos completada")
        except Exception as e:
            logging.error(f"Error en _load_data_thread: {e}")
            Clock.schedule_once(lambda dt: self.show_popup("Error", f"Error cargando datos: {e}", is_error=True))

    def build_ui(self):
        """Build the user interface with sync status"""
        try:
            # Sync status bar
            sync_bar = BoxLayout(size_hint_y=None, height=dp(30), spacing=10)
            self.sync_status_label = Label(text='🔴 Offline', size_hint_x=0.3, color=ERROR_COLOR)
            self.pending_sync_label = Label(text='Pendientes: 0', size_hint_x=0.3, color=ORANGE_COLOR)
            
            sync_now_btn = Button(text='Sincronizar Ahora', size_hint_x=0.4, size_hint_y=None, height=dp(30),
                                 color=WHITE_TEXT_COLOR, background_color=TAB_ACTIVE_COLOR)
            sync_now_btn.bind(on_press=self.manual_sync)
            
            sync_bar.add_widget(self.sync_status_label)
            sync_bar.add_widget(self.pending_sync_label)
            sync_bar.add_widget(sync_now_btn)
            self.add_widget(sync_bar)

            # User info
            user_info = Label(text=f'Usuario: {self.app_instance.current_user}', 
                             size_hint_y=None, height=dp(30), color=TEXT_COLOR)
            self.add_widget(user_info)

            # Input card
            input_card = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
            input_card.bind(minimum_height=input_card.setter('height'))
            
            # Fields layout
            fields_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=dp(280))
            
            self.codigo_barras_input = TextInput(hint_text='Escanear código y presionar Enter...', 
                                               multiline=False)
            self.codigo_barras_input.bind(on_text_validate=self.process_barcode_entry)
            
            self.descripcion_input = TextInput(hint_text='Descripción (auto)', readonly=True, multiline=False)
            self.qty_input = TextInput(hint_text='Cant.', input_type='number', multiline=False)
            self.qty_input.bind(on_text_validate=self.add_or_update_record)
            
            self.auditor_input = TextInput(hint_text='Auditor', multiline=False)
            self.auditor_input.text = self.app_instance.current_user  # Set current user as default auditor
            
            self.locacion_spinner = Spinner(text='Selecciona Locación', values=[], 
                                          size_hint_y=None, height=dp(44), 
                                          color=WHITE_TEXT_COLOR, background_color=TAB_ACTIVE_COLOR)
            
            widgets = [
                ('Código:', self.codigo_barras_input), 
                ('Descripción:', self.descripcion_input), 
                ('Cantidad:', self.qty_input), 
                ('Auditor:', self.auditor_input), 
                ('Locación:', self.locacion_spinner)
            ]
            
            for label_text, widget in widgets: 
                fields_layout.add_widget(Label(text=label_text, size_hint_x=0.3, halign='right', color=TEXT_COLOR))
                fields_layout.add_widget(widget)
            
            input_card.add_widget(fields_layout)
            
            # Buttons
            buttons_layout = GridLayout(cols=3, size_hint_y=None, height=dp(44), spacing=10)
            self.add_button = Button(text='Agregar', color=WHITE_TEXT_COLOR, background_color=SUCCESS_COLOR)
            self.add_button.bind(on_press=self.add_or_update_record)
            
            self.delete_button = Button(text='Borrar', color=WHITE_TEXT_COLOR, 
                                      background_color=ERROR_COLOR, disabled=True, opacity=0)
            self.delete_button.bind(on_press=self.delete_record)
            
            self.cancel_button = Button(text='Cancelar', color=TEXT_COLOR, disabled=True, opacity=0)
            self.cancel_button.bind(on_press=self.clear_fields)
            
            buttons_layout.add_widget(self.add_button)
            buttons_layout.add_widget(self.delete_button)
            buttons_layout.add_widget(self.cancel_button)
            input_card.add_widget(buttons_layout)
            
            self.status_label = Label(text="", font_size='14sp', size_hint_y=None, height=dp(30))
            input_card.add_widget(self.status_label)
            
            self.add_widget(input_card)
            
            # Search panel
            search_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(90), padding=10, spacing=5)
            search_panel.add_widget(Label(text='Buscar en Conteos:', size_hint_y=None, height=dp(20), 
                                        bold=True, color=TEXT_COLOR))
            search_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=10)
            self.search_input_counts = TextInput(hint_text='Buscar por código, desc, auditor, locación...', 
                                               multiline=False)
            self.search_input_counts.bind(on_text_validate=self._filter_and_display_records)
            
            clear_search_btn = Button(text='Limpiar', size_hint_x=0.25)
            clear_search_btn.bind(on_press=self._clear_search_and_display)
            
            search_bar.add_widget(self.search_input_counts)
            search_bar.add_widget(clear_search_btn)
            search_panel.add_widget(search_bar)
            self.add_widget(search_panel)

            self.add_widget(Label(text='Últimos Registros:', size_hint_y=None, height=dp(30), 
                                bold=True, color=TEXT_COLOR))
            
            # Table
            scroll_view = ScrollView()
            self.table_layout = GridLayout(cols=6, size_hint_y=None, row_default_height=dp(40), spacing=1)  # Added sync status column
            self.table_layout.bind(minimum_height=self.table_layout.setter('height'))
            scroll_view.add_widget(self.table_layout)
            self.add_widget(scroll_view)
            
            logging.info("UI construida exitosamente")
            
        except Exception as e:
            logging.error(f"Error building UI: {e}")
            logging.error(traceback.format_exc())

    def manual_sync(self, instance):
        """Manual synchronization trigger"""
        if self.app_instance.firebase_enabled:
            Thread(target=self._sync_with_firebase, daemon=True).start()
        else:
            self.show_popup("Info", "Firebase no está configurado. Trabajando en modo offline.", is_error=False)

    def _sync_with_firebase(self, dt=None):
        """Sync with Firebase"""
        try:
            if not self.app_instance.firebase_enabled or not self.app_instance.firebase_manager:
                return

            # Update sync status
            Clock.schedule_once(lambda dt: self._update_sync_status('syncing'))
            
            # Sync pending records
            success_count = self.db_manager.sync_pending_records(self.app_instance.firebase_manager)
            
            # Update UI
            def update_sync_ui(dt):
                if success_count > 0:
                    self._update_sync_status('online')
                    self.status_label.text = f'Sincronizados {success_count} registros'
                    self.status_label.color = SUCCESS_COLOR
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 3)
                else:
                    self._update_sync_status('offline' if not self.app_instance.firebase_manager.is_online() else 'online')
                
                self._update_pending_sync_count()
                self._display_last_records()
            
            Clock.schedule_once(update_sync_ui)
            
        except Exception as e:
            logging.error(f"Error syncing with Firebase: {e}")
            Clock.schedule_once(lambda dt: self._update_sync_status('error'))

    @mainthread
    def _update_sync_status(self, status):
        """Update sync status indicator"""
        if status == 'online':
            self.sync_status_label.text = '🟢 Online'
            self.sync_status_label.color = SUCCESS_COLOR
        elif status == 'syncing':
            self.sync_status_label.text = '🟡 Sincronizando...'
            self.sync_status_label.color = ORANGE_COLOR
        elif status == 'error':
            self.sync_status_label.text = '🔴 Error'
            self.sync_status_label.color = ERROR_COLOR
        else:  # offline
            self.sync_status_label.text = '🔴 Offline'
            self.sync_status_label.color = ERROR_COLOR

    def _update_pending_sync_count(self):
        """Update pending sync count"""
        try:
            count = self.db_manager.get_pending_sync_count()
            Clock.schedule_once(lambda dt: setattr(self.pending_sync_label, 'text', f'Pendientes: {count}'))
        except Exception as e:
            logging.error(f"Error updating pending sync count: {e}")

    def add_or_update_record(self, instance=None):
        """Add or update inventory record with sync support"""
        try:
            # Validate inputs
            codigo_barras = self.codigo_barras_input.text.strip()
            descripcion = self.descripcion_input.text.strip()
            cantidad_text = self.qty_input.text.strip()
            auditor = self.auditor_input.text.strip()
            locacion = self.locacion_spinner.text if self.locacion_spinner.text != 'Selecciona Locación' else ''

            if not codigo_barras:
                Clock.schedule_once(lambda dt: self.show_popup("Error", "El código de barras es obligatorio.", is_error=True))
                return

            if not cantidad_text:
                Clock.schedule_once(lambda dt: self.show_popup("Error", "La cantidad es obligatoria.", is_error=True))
                return

            try:
                cantidad = int(cantidad_text)
            except ValueError:
                Clock.schedule_once(lambda dt: self.show_popup("Error", "La cantidad debe ser un número entero.", is_error=True))
                return

            # Update UI status immediately
            self.status_label.text = "Guardando..."
            self.status_label.color = ORANGE_COLOR

            # Save record in background thread
            def save_record_async():
                try:
                    if self.editing_id:
                        success = self.db_manager.update_record(self.editing_id, codigo_barras, descripcion, cantidad, auditor, locacion)
                        message = "Registro actualizado correctamente" if success else "Error al actualizar el registro"
                    else:
                        success = self.db_manager.add_record_with_sync(codigo_barras, descripcion, cantidad, auditor, locacion, 
                                                                     self.app_instance.current_user)
                        message = "Registro agregado correctamente" if success else "Error al guardar el registro"
                    
                    # Update UI in main thread
                    Clock.schedule_once(lambda dt: self._on_record_saved(success, message))
                    
                    # Update pending count
                    self._update_pending_sync_count()
                    
                except Exception as e:
                    logging.error(f"Error in save_record_async: {e}")
                    Clock.schedule_once(lambda dt: self._on_record_saved(False, f"Error: {e}"))

            # Start background thread
            Thread(target=save_record_async, daemon=True).start()
                
        except Exception as e:
            logging.error(f"Error in add_or_update_record: {e}")
            Clock.schedule_once(lambda dt: self.show_popup("Error", f"Error agregando registro: {e}", is_error=True))

    @mainthread
    def _on_record_saved(self, success, message):
        """Handle record save completion in main thread"""
        try:
            if success:
                self.clear_fields()
                self._display_last_records()
                self.status_label.text = message
                self.status_label.color = SUCCESS_COLOR
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 3)
                
                # Try immediate sync if online
                if self.app_instance.firebase_enabled:
                    Thread(target=self._sync_with_firebase, daemon=True).start()
            else:
                self.status_label.text = ""
                self.show_popup("Error", message, is_error=True)
        except Exception as e:
            logging.error(f"Error in _on_record_saved: {e}")

    # ... (rest of the methods remain similar but with sync status column added to display)

    @mainthread
    def _display_last_records(self):
        """Display last records in table with sync status"""
        try:
            self.table_layout.clear_widgets()
            
            # Header
            headers = ['Código', 'Descripción', 'Cantidad', 'Auditor', 'Locación', 'Sync']
            for header in headers:
                label = Label(text=header, bold=True, color=TEXT_COLOR, size_hint_y=None, height=dp(40))
                with label.canvas.before:
                    Color(*TAB_ACTIVE_COLOR)
                    Rectangle(size=label.size, pos=label.pos)
                label.bind(size=self._update_rect, pos=self._update_rect)
                self.table_layout.add_widget(label)
            
            # Data rows
            records = self.db_manager.get_last_records_with_sync_status(50)
            for i, record in enumerate(records):
                bg_color = ALT_ROW_COLOR if i % 2 == 0 else CARD_BG_COLOR
                
                for j, value in enumerate(record[1:7]):  # Skip ID, include sync status
                    if j == 1:  # Description column
                        display_text = truncate_text(value, 20)
                    elif j == 5:  # Sync status column
                        display_text = '✅' if value == 1 else '⏳'
                    else:
                        display_text = truncate_text(value, 15)
                    
                    label = Label(text=str(display_text), color=TEXT_COLOR, 
                                size_hint_y=None, height=dp(40))
                    
                    with label.canvas.before:
                        Color(*bg_color)
                        Rectangle(size=label.size, pos=label.pos)
                    label.bind(size=self._update_rect, pos=self._update_rect)
                    
                    # Make row clickable
                    label.record_id = record[0]
                    label.bind(on_touch_down=self._on_record_touch)
                    
                    self.table_layout.add_widget(label)
                    
        except Exception as e:
            logging.error(f"Error displaying records: {e}")

    def show_popup(self, title, message, is_error=False):
        """Show popup message"""
        try:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            try:
                with content.canvas.before:
                    Color(*POPUP_BG_COLOR)
                    self.popup_rect = Rectangle(size=content.size, pos=content.pos)
                content.bind(pos=self._update_rect_popup, size=self._update_rect_popup)
            except Exception as e:
                logging.warning(f"Could not set popup canvas: {e}")
            
            msg_label = Label(text=str(message), halign='center', valign='middle', 
                            color=WHITE_TEXT_COLOR, markup=True)
            try:
                msg_label.bind(size=lambda *x: msg_label.setter('text_size')(msg_label, (content.width - 20, None)))
            except Exception as e:
                logging.warning(f"Could not bind label size: {e}")
            
            btn = Button(text='Cerrar', size_hint_y=None, height=dp(44))
            btn.color = WHITE_TEXT_COLOR
            if is_error:
                btn.background_color = ERROR_COLOR
            else:
                btn.background_color = TAB_ACTIVE_COLOR
            
            content.add_widget(msg_label)
            content.add_widget(btn)
            
            popup = Popup(title=title, content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
            popup.title_color = WHITE_TEXT_COLOR
            popup.separator_color = TAB_ACTIVE_COLOR
            try:
                btn.bind(on_press=popup.dismiss)
            except Exception as e:
                logging.warning(f"Could not bind button press: {e}")
            popup.open()
            
        except Exception as e:
            logging.error(f"Error showing popup: {e}")

    def _update_rect_popup(self, instance, value):
        if hasattr(self, 'popup_rect'):
            self.popup_rect.pos = instance.pos
            self.popup_rect.size = instance.size

    def _update_rect(self, instance, rect):
        rect.pos = instance.pos
        rect.size = instance.size

    # ... (implement remaining methods similar to original but with sync support)

    def process_barcode_entry(self, instance):
        """Process barcode entry"""
        try:
            barcode = self.codigo_barras_input.text.strip()
            if not barcode: 
                return
                
            master_screen = self.app_instance.master_screen
            
            if not (master_screen and hasattr(master_screen, 'master_dict')):
                self.show_popup("Error", "El maestro de artículos no está cargado.", is_error=True)
                return
                
            description = master_screen.master_dict.get(barcode)
            if description is not None:
                self.descripcion_input.text = description
                self.qty_input.focus = True
            else: 
                self.open_new_item_popup(barcode)
                
        except Exception as e:
            logging.error(f"Error processing barcode: {e}")
            self.show_popup("Error", f"Error procesando código: {e}", is_error=True)

    def open_new_item_popup(self, barcode):
        """Open popup for new item"""
        try:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            try:
                with content.canvas.before: 
                    Color(*POPUP_BG_COLOR)
                    self.popup_rect = Rectangle(size=content.size, pos=content.pos)
                content.bind(pos=self._update_rect_popup, size=self._update_rect_popup)
            except Exception as e:
                logging.warning(f"Could not set popup canvas: {e}")
            
            content.add_widget(Label(text=f"Artículo no encontrado.\nCódigo: [b]{barcode}[/b]", 
                                   markup=True, color=WHITE_TEXT_COLOR))
            
            desc_input = TextInput(hint_text='Ingrese la nueva descripción...', multiline=False, 
                                 size_hint_y=None, height=dp(44))
            content.add_widget(desc_input)
            
            buttons_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=10)
            popup = Popup(title='Agregar Artículo al Master', content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
            
            def save_action(instance):
                new_desc = desc_input.text.strip()
                if new_desc: 
                    self._add_item_to_master_and_continue(barcode, new_desc)
                    popup.dismiss()
            
            def cancel_action(instance):
                self.codigo_barras_input.text = ''
                self.codigo_barras_input.focus = True
                popup.dismiss()
                
            save_btn = Button(text='Guardar', color=WHITE_TEXT_COLOR, background_color=SUCCESS_COLOR)
            save_btn.bind(on_press=save_action)
            cancel_btn = Button(text='Cancelar', color=WHITE_TEXT_COLOR, background_color=ERROR_COLOR)
            cancel_btn.bind(on_press=cancel_action)
            
            buttons_layout.add_widget(save_btn)
            buttons_layout.add_widget(cancel_btn)
            content.add_widget(buttons_layout)
            
            popup.title_color = WHITE_TEXT_COLOR
            popup.separator_color = TAB_ACTIVE_COLOR
            popup.open()
            
        except Exception as e:
            logging.error(f"Error opening new item popup: {e}")
            self.show_popup("Error", f"Error abriendo ventana: {e}", is_error=True)

    def _add_item_to_master_and_continue(self, barcode, description):
        """Add item to master and continue with inventory entry"""
        try:
            master_screen = self.app_instance.master_screen
            
            if master_screen and hasattr(master_screen, 'master_dict'):
                master_screen.master_dict[barcode] = description
                master_screen._save_master_to_file()
                
            self.descripcion_input.text = description
            self.qty_input.focus = True
            
        except Exception as e:
            logging.error(f"Error adding item to master: {e}")
            self.show_popup("Error", f"Error agregando al maestro: {e}", is_error=True)

    def clear_fields(self, instance=None):
        """Clear all input fields"""
        try:
            self.codigo_barras_input.text = ''
            self.descripcion_input.text = ''
            self.qty_input.text = ''
            self.locacion_spinner.text = 'Selecciona Locación'
            self.editing_id = None
            
            # Reset buttons
            self.add_button.text = 'Agregar'
            self.delete_button.disabled = True
            self.delete_button.opacity = 0
            self.cancel_button.disabled = True
            self.cancel_button.opacity = 0
            
            self.codigo_barras_input.focus = True
            
        except Exception as e:
            logging.error(f"Error clearing fields: {e}")

    def delete_record(self, instance=None):
        """Delete selected record"""
        try:
            if self.editing_id:
                success = self.db_manager.delete_record(self.editing_id)
                if success:
                    self.clear_fields()
                    self._display_last_records()
                    self.status_label.text = "Registro eliminado"
                    self.status_label.color = ERROR_COLOR
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 3)
                else:
                    self.show_popup("Error", "Error al eliminar el registro", is_error=True)
                    
        except Exception as e:
            logging.error(f"Error deleting record: {e}")
            self.show_popup("Error", f"Error eliminando registro: {e}", is_error=True)

    def _filter_and_display_records(self, instance=None):
        """Filter and display records based on search"""
        try:
            search_text = self.search_input_counts.text.strip()
            if search_text:
                records = self.db_manager.search_records(search_text)
                self._display_filtered_records(records)
            else:
                self._display_last_records()
                
        except Exception as e:
            logging.error(f"Error filtering records: {e}")

    def _clear_search_and_display(self, instance=None):
        """Clear search and display all records"""
        try:
            self.search_input_counts.text = ''
            self._display_last_records()
            
        except Exception as e:
            logging.error(f"Error clearing search: {e}")

    @mainthread
    def _display_filtered_records(self, records):
        """Display filtered records with sync status"""
        try:
            self.table_layout.clear_widgets()
            
            # Header
            headers = ['Código', 'Descripción', 'Cantidad', 'Auditor', 'Locación', 'Sync']
            for header in headers:
                label = Label(text=header, bold=True, color=TEXT_COLOR, size_hint_y=None, height=dp(40))
                with label.canvas.before:
                    Color(*TAB_ACTIVE_COLOR)
                    Rectangle(size=label.size, pos=label.pos)
                label.bind(size=self._update_rect, pos=self._update_rect)
                self.table_layout.add_widget(label)
            
            # Data rows
            for i, record in enumerate(records):
                bg_color = ALT_ROW_COLOR if i % 2 == 0 else CARD_BG_COLOR
                
                for j, value in enumerate(record[1:7]):  # Skip ID, include sync status
                    if j == 1:  # Description column
                        display_text = truncate_text(value, 20)
                    elif j == 5:  # Sync status column
                        display_text = '✅' if value == 1 else '⏳'
                    else:
                        display_text = truncate_text(value, 15)
                    
                    label = Label(text=str(display_text), color=TEXT_COLOR, 
                                size_hint_y=None, height=dp(40))
                    
                    with label.canvas.before:
                        Color(*bg_color)
                        Rectangle(size=label.size, pos=label.pos)
                    label.bind(size=self._update_rect, pos=self._update_rect)
                    
                    # Make row clickable
                    if len(record) > 0:
                        label.record_id = record[0]
                        label.bind(on_touch_down=self._on_record_touch)
                    
                    self.table_layout.add_widget(label)
                    
        except Exception as e:
            logging.error(f"Error displaying filtered records: {e}")

    def _on_record_touch(self, instance, touch):
        """Handle record touch for editing"""
        try:
            if instance.collide_point(*touch.pos):
                record = self.db_manager.get_record_by_id(instance.record_id)
                if record:
                    self._load_record_for_editing(record)
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error on record touch: {e}")

    def _load_record_for_editing(self, record):
        """Load record data for editing"""
        try:
            self.editing_id = record[0]
            self.codigo_barras_input.text = record[1]
            self.descripcion_input.text = record[2] or ''
            self.qty_input.text = str(record[3])
            self.auditor_input.text = record[4] or ''
            self.locacion_spinner.text = record[5] or 'Selecciona Locación'
            
            # Update buttons
            self.add_button.text = 'Actualizar'
            self.delete_button.disabled = False
            self.delete_button.opacity = 1
            self.cancel_button.disabled = False
            self.cancel_button.opacity = 1
            
        except Exception as e:
            logging.error(f"Error loading record for editing: {e}")

    def _load_last_values_to_ui(self):
        """Load last values to UI inputs"""
        try:
            last_values = self.db_manager.get_last_values()
            if last_values:
                Clock.schedule_once(lambda dt: self._update_ui_with_last_values(last_values))
                
        except Exception as e:
            logging.error(f"Error loading last values: {e}")

    @mainthread
    def _update_ui_with_last_values(self, last_values):
        """Update UI with last values"""
        try:
            if last_values.get('locacion'):
                self.locacion_spinner.text = last_values['locacion']
                
        except Exception as e:
            logging.error(f"Error updating UI with last values: {e}")


# --- Enhanced Master Screen ---
class MasterScreen(BoxLayout):
    master_dict = DictProperty({})

    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        self.app_instance = app_instance
        self.build_ui()

    def build_ui(self):
        """Build master screen UI"""
        try:
            # File loading section
            file_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), 
                                   padding=10, spacing=10)
            
            file_section.add_widget(Label(text='Cargar Archivo Master:', size_hint_y=None, height=dp(30), 
                                        bold=True, color=TEXT_COLOR))
            
            load_btn = Button(text='Cargar Master desde Excel', size_hint_y=None, height=dp(44),
                            color=WHITE_TEXT_COLOR, background_color=TAB_ACTIVE_COLOR)
            load_btn.bind(on_press=self.load_master_file)
            file_section.add_widget(load_btn)
            
            self.master_status = Label(text='No hay master cargado', size_hint_y=None, height=dp(30),
                                     color=ERROR_COLOR)
            file_section.add_widget(self.master_status)
            
            self.add_widget(file_section)
            
            # Master data display
            self.add_widget(Label(text='Datos del Master:', size_hint_y=None, height=dp(30), 
                                bold=True, color=TEXT_COLOR))
            
            # Search in master
            search_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=10, padding=10)
            self.search_master_input = TextInput(hint_text='Buscar en master...', multiline=False)
            self.search_master_input.bind(on_text_validate=self._filter_master_display)
            
            clear_master_search = Button(text='Limpiar', size_hint_x=0.25)
            clear_master_search.bind(on_press=self._clear_master_search)
            
            search_layout.add_widget(self.search_master_input)
            search_layout.add_widget(clear_master_search)
            self.add_widget(search_layout)
            
            # Master table
            scroll_view = ScrollView()
            self.master_table = GridLayout(cols=2, size_hint_y=None, row_default_height=dp(40), spacing=1)
            self.master_table.bind(minimum_height=self.master_table.setter('height'))
            scroll_view.add_widget(self.master_table)
            self.add_widget(scroll_view)
            
        except Exception as e:
            logging.error(f"Error building master UI: {e}")

    def load_master_file(self, instance=None):
        """Load master file"""
        try:
            if HAS_PLYER_FILECHOOSER:
                self._load_with_plyer()
            else:
                self._load_with_kivy_chooser()
                
        except Exception as e:
            logging.error(f"Error loading master file: {e}")
            self.show_popup("Error", f"Error cargando archivo: {e}", is_error=True)

    def _load_with_plyer(self):
        """Load file using plyer filechooser"""
        try:
            android_utils.request_storage_permissions()
            
            def on_file_selected(selection):
                if selection:
                    file_path = selection[0]
                    self._process_master_file(file_path)
            
            filechooser.open_file(on_selection=on_file_selected, 
                                filters=['*.xlsx', '*.xls'])
                                
        except Exception as e:
            logging.error(f"Error with plyer filechooser: {e}")
            self._load_with_kivy_chooser()

    def _load_with_kivy_chooser(self):
        """Load file using Kivy filechooser"""
        try:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            filechooser = FileChooserListView(filters=['*.xlsx', '*.xls'])
            content.add_widget(filechooser)
            
            buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=10)
            
            def load_selected(instance):
                if filechooser.selection:
                    popup.dismiss()
                    self._process_master_file(filechooser.selection[0])
            
            load_btn = Button(text='Cargar', color=WHITE_TEXT_COLOR, background_color=SUCCESS_COLOR)
            load_btn.bind(on_press=load_selected)
            
            cancel_btn = Button(text='Cancelar', color=WHITE_TEXT_COLOR, background_color=ERROR_COLOR)
            
            buttons.add_widget(load_btn)
            buttons.add_widget(cancel_btn)
            content.add_widget(buttons)
            
            popup = Popup(title='Seleccionar Archivo Master', content=content, 
                         size_hint=(0.9, 0.8), auto_dismiss=False)
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            logging.error(f"Error with Kivy filechooser: {e}")
            self.show_popup("Error", f"Error abriendo selector de archivos: {e}", is_error=True)

    def _process_master_file(self, file_path):
        """Process master file in background thread"""
        try:
            loading_popup = LoadingPopup()
            loading_popup.open()
            
            def process_in_background():
                try:
                    success, data_or_error = file_manager.load_excel_file(file_path)
                    
                    def update_ui(dt):
                        loading_popup.dismiss()
                        if success:
                            self.master_dict = data_or_error
                            self._save_master_to_file()
                            self._display_master_data()
                            self.master_status.text = f'Master cargado: {len(self.master_dict)} artículos'
                            self.master_status.color = SUCCESS_COLOR
                        else:
                            self.show_popup("Error", f"Error cargando archivo: {data_or_error}", is_error=True)
                    
                    Clock.schedule_once(update_ui)
                    
                except Exception as e:
                    logging.error(f"Error processing master file: {e}")
                    Clock.schedule_once(lambda dt: (
                        loading_popup.dismiss(),
                        self.show_popup("Error", f"Error procesando archivo: {e}", is_error=True)
                    ))
            
            Thread(target=process_in_background, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Error in _process_master_file: {e}")
            self.show_popup("Error", f"Error iniciando carga: {e}", is_error=True)

    def _save_master_to_file(self):
        """Save master dict to JSON file"""
        try:
            master_file = file_manager.get_master_file_path()
            with open(master_file, 'w', encoding='utf-8') as f:
                json.dump(self.master_dict, f, ensure_ascii=False, indent=2)
            logging.info(f"Master guardado en: {master_file}")
            
        except Exception as e:
            logging.error(f"Error saving master to file: {e}")

    def _load_master_from_file(self):
        """Load master dict from JSON file"""
        try:
            master_file = file_manager.get_master_file_path()
            if os.path.exists(master_file):
                with open(master_file, 'r', encoding='utf-8') as f:
                    self.master_dict = json.load(f)
                self.master_status.text = f'Master cargado: {len(self.master_dict)} artículos'
                self.master_status.color = SUCCESS_COLOR
                self._display_master_data()
                logging.info(f"Master cargado desde: {master_file}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error loading master from file: {e}")
            return False

    @mainthread
    def _display_master_data(self):
        """Display master data in table"""
        try:
            self.master_table.clear_widgets()
            
            # Header
            headers = ['Código', 'Descripción']
            for header in headers:
                label = Label(text=header, bold=True, color=TEXT_COLOR, size_hint_y=None, height=dp(40))
                with label.canvas.before:
                    Color(*TAB_ACTIVE_COLOR)
                    Rectangle(size=label.size, pos=label.pos)
                label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(label)
            
            # Data rows (limit to first 100 for performance)
            items = list(self.master_dict.items())[:100]
            for i, (codigo, descripcion) in enumerate(items):
                bg_color = ALT_ROW_COLOR if i % 2 == 0 else CARD_BG_COLOR
                
                # Código
                codigo_label = Label(text=truncate_text(codigo, 15), color=TEXT_COLOR, 
                                   size_hint_y=None, height=dp(40))
                with codigo_label.canvas.before:
                    Color(*bg_color)
                    Rectangle(size=codigo_label.size, pos=codigo_label.pos)
                codigo_label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(codigo_label)
                
                # Descripción
                desc_label = Label(text=truncate_text(descripcion, 30), color=TEXT_COLOR, 
                                 size_hint_y=None, height=dp(40))
                with desc_label.canvas.before:
                    Color(*bg_color)
                    Rectangle(size=desc_label.size, pos=desc_label.pos)
                desc_label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(desc_label)
                
            if len(self.master_dict) > 100:
                # Add note about limited display
                note_label = Label(text=f'Mostrando 100 de {len(self.master_dict)} artículos', 
                                 color=ORANGE_COLOR, size_hint_y=None, height=dp(40))
                self.master_table.add_widget(note_label)
                self.master_table.add_widget(Label(text='', size_hint_y=None, height=dp(40)))
                
        except Exception as e:
            logging.error(f"Error displaying master data: {e}")

    def _filter_master_display(self, instance=None):
        """Filter master display based on search"""
        try:
            search_text = self.search_master_input.text.strip().lower()
            if search_text:
                filtered_items = {k: v for k, v in self.master_dict.items() 
                                if search_text in k.lower() or search_text in v.lower()}
                self._display_filtered_master(filtered_items)
            else:
                self._display_master_data()
                
        except Exception as e:
            logging.error(f"Error filtering master display: {e}")

    def _clear_master_search(self, instance=None):
        """Clear master search"""
        try:
            self.search_master_input.text = ''
            self._display_master_data()
            
        except Exception as e:
            logging.error(f"Error clearing master search: {e}")

    @mainthread
    def _display_filtered_master(self, filtered_items):
        """Display filtered master items"""
        try:
            self.master_table.clear_widgets()
            
            # Header
            headers = ['Código', 'Descripción']
            for header in headers:
                label = Label(text=header, bold=True, color=TEXT_COLOR, size_hint_y=None, height=dp(40))
                with label.canvas.before:
                    Color(*TAB_ACTIVE_COLOR)
                    Rectangle(size=label.size, pos=label.pos)
                label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(label)
            
            # Data rows
            for i, (codigo, descripcion) in enumerate(filtered_items.items()):
                bg_color = ALT_ROW_COLOR if i % 2 == 0 else CARD_BG_COLOR
                
                # Código
                codigo_label = Label(text=truncate_text(codigo, 15), color=TEXT_COLOR, 
                                   size_hint_y=None, height=dp(40))
                with codigo_label.canvas.before:
                    Color(*bg_color)
                    Rectangle(size=codigo_label.size, pos=codigo_label.pos)
                codigo_label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(codigo_label)
                
                # Descripción
                desc_label = Label(text=truncate_text(descripcion, 30), color=TEXT_COLOR, 
                                 size_hint_y=None, height=dp(40))
                with desc_label.canvas.before:
                    Color(*bg_color)
                    Rectangle(size=desc_label.size, pos=desc_label.pos)
                desc_label.bind(size=self._update_rect, pos=self._update_rect)
                self.master_table.add_widget(desc_label)
                
        except Exception as e:
            logging.error(f"Error displaying filtered master: {e}")

    def show_popup(self, title, message, is_error=False):
        """Show popup message"""
        try:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            try:
                with content.canvas.before:
                    Color(*POPUP_BG_COLOR)
                    self.popup_rect = Rectangle(size=content.size, pos=content.pos)
                content.bind(pos=self._update_rect_popup, size=self._update_rect_popup)
            except Exception as e:
                logging.warning(f"Could not set popup canvas: {e}")
            
            msg_label = Label(text=str(message), halign='center', valign='middle', 
                            color=WHITE_TEXT_COLOR, markup=True)
            try:
                msg_label.bind(size=lambda *x: msg_label.setter('text_size')(msg_label, (content.width - 20, None)))
            except Exception as e:
                logging.warning(f"Could not bind label size: {e}")
            
            btn = Button(text='Cerrar', size_hint_y=None, height=dp(44))
            btn.color = WHITE_TEXT_COLOR
            if is_error:
                btn.background_color = ERROR_COLOR
            else:
                btn.background_color = TAB_ACTIVE_COLOR
            
            content.add_widget(msg_label)
            content.add_widget(btn)
            
            popup = Popup(title=title, content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
            popup.title_color = WHITE_TEXT_COLOR
            popup.separator_color = TAB_ACTIVE_COLOR
            try:
                btn.bind(on_press=popup.dismiss)
            except Exception as e:
                logging.warning(f"Could not bind button press: {e}")
            popup.open()
            
        except Exception as e:
            logging.error(f"Error showing popup: {e}")

    def _update_rect_popup(self, instance, value):
        if hasattr(self, 'popup_rect'):
            self.popup_rect.pos = instance.pos
            self.popup_rect.size = instance.size

    def _update_rect(self, instance, rect):
        rect.pos = instance.pos
        rect.size = instance.size


# --- Pop-up de carga (LoadingPopup) ---
class LoadingPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Cargando...'
        self.content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Simple loading indicator
        loading_label = Label(text="Por favor, espere...", color=WHITE_TEXT_COLOR)
        self.content.add_widget(loading_label)
        
        self.size_hint = (0.7, 0.3)
        self.auto_dismiss = False
        self.title_color = WHITE_TEXT_COLOR
        self.separator_color = TAB_ACTIVE_COLOR
        
        # Add background color safely
        try:
            with self.content.canvas.before:
                Color(*POPUP_BG_COLOR)
                self.rect = Rectangle(size=self.content.size, pos=self.content.pos)
        except Exception as e:
            logging.warning(f"Could not set popup background: {e}")
        
        try:
            self.content.bind(size=self._update_rect, pos=self._update_rect)
        except Exception as e:
            logging.warning(f"Could not bind popup events: {e}")
    
    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos


# --- Enhanced Inventory App with Firebase Integration ---
class InventoryApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.firebase_enabled = False
        self.firebase_manager = None
        self.current_user = None
        self.current_screen = None

    def build(self):
        """Build the main application"""
        try:
            logging.info("Iniciando aplicación de inventario con Firebase")
            
            # Request permissions on Android
            android_utils.request_storage_permissions()
            
            # Check for existing Firebase configuration
            if self._check_firebase_config():
                self.initialize_firebase_and_login()
            else:
                self.show_firebase_config()
            
            return BoxLayout()  # Empty layout, will be replaced by screens
            
        except Exception as e:
            logging.error(f"Error building app: {e}")
            logging.error(traceback.format_exc())
            raise

    def _check_firebase_config(self):
        """Check if Firebase configuration exists"""
        try:
            config_file = os.path.join(android_utils.get_data_directory(), 'firebase_config.json')
            return os.path.exists(config_file)
        except Exception as e:
            logging.error(f"Error checking Firebase config: {e}")
            return False

    def show_firebase_config(self):
        """Show Firebase configuration screen"""
        try:
            self.current_screen = FirebaseConfigScreen(self)
            self.root.clear_widgets()
            self.root.add_widget(self.current_screen)
        except Exception as e:
            logging.error(f"Error showing Firebase config: {e}")

    def initialize_firebase_and_login(self):
        """Initialize Firebase and show login screen"""
        try:
            config_file = os.path.join(android_utils.get_data_directory(), 'firebase_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                if HAS_FIREBASE:
                    self.firebase_manager = FirebaseManager(config)
                    self.firebase_enabled = True
                    logging.info("Firebase inicializado correctamente")
                else:
                    logging.warning("Firebase no disponible, continuando en modo offline")
            
            self.show_login_screen()
            
        except Exception as e:
            logging.error(f"Error initializing Firebase: {e}")
            self.show_login_screen()

    def show_login_screen(self):
        """Show login screen"""
        try:
            self.current_screen = LoginScreen(self)
            self.root.clear_widgets()
            self.root.add_widget(self.current_screen)
        except Exception as e:
            logging.error(f"Error showing login screen: {e}")

    def show_main_screen(self):
        """Show main application screen"""
        try:
            # Main container
            main_layout = BoxLayout(orientation='vertical')
            
            # Top bar with user info and logout
            top_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=10, padding=5)
            
            user_label = Label(text=f'Usuario: {self.current_user}', color=TEXT_COLOR, size_hint_x=0.7)
            logout_btn = Button(text='Cerrar Sesión', size_hint_x=0.3, size_hint_y=None, height=dp(30),
                               color=WHITE_TEXT_COLOR, background_color=ERROR_COLOR)
            logout_btn.bind(on_press=self.logout)
            
            top_bar.add_widget(user_label)
            top_bar.add_widget(logout_btn)
            main_layout.add_widget(top_bar)
            
            # Tab buttons
            tab_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=2)
            
            self.inventory_tab = Button(text='Conteo', color=WHITE_TEXT_COLOR, 
                                      background_color=TAB_ACTIVE_COLOR)
            self.master_tab = Button(text='Master', color=TEXT_COLOR, 
                                   background_color=TAB_INACTIVE_COLOR)
            
            self.inventory_tab.bind(on_press=self.switch_to_inventory)
            self.master_tab.bind(on_press=self.switch_to_master)
            
            tab_layout.add_widget(self.inventory_tab)
            tab_layout.add_widget(self.master_tab)
            main_layout.add_widget(tab_layout)
            
            # Screens container
            self.screens_container = BoxLayout()
            
            # Create screens
            self.inventory_screen = InventoryScreen(self)
            self.master_screen = MasterScreen(self)
            
            # Show inventory screen initially
            self.screens_container.add_widget(self.inventory_screen)
            main_layout.add_widget(self.screens_container)
            
            # Replace current screen
            self.current_screen = main_layout
            self.root.clear_widgets()
            self.root.add_widget(main_layout)
            
            # Load master data if available
            Clock.schedule_once(self._delayed_master_load, 0.5)
            
            logging.info("Pantalla principal cargada exitosamente")
            
        except Exception as e:
            logging.error(f"Error showing main screen: {e}")
            logging.error(traceback.format_exc())

    def _delayed_master_load(self, dt):
        """Load master data after app is fully initialized"""
        try:
            self.master_screen._load_master_from_file()
        except Exception as e:
            logging.error(f"Error loading master data: {e}")

    def switch_to_inventory(self, instance=None):
        """Switch to inventory screen"""
        try:
            self.screens_container.clear_widgets()
            self.screens_container.add_widget(self.inventory_screen)
            
            self.inventory_tab.background_color = TAB_ACTIVE_COLOR
            self.inventory_tab.color = WHITE_TEXT_COLOR
            self.master_tab.background_color = TAB_INACTIVE_COLOR
            self.master_tab.color = TEXT_COLOR
            
        except Exception as e:
            logging.error(f"Error switching to inventory: {e}")

    def switch_to_master(self, instance=None):
        """Switch to master screen"""
        try:
            self.screens_container.clear_widgets()
            self.screens_container.add_widget(self.master_screen)
            
            self.master_tab.background_color = TAB_ACTIVE_COLOR
            self.master_tab.color = WHITE_TEXT_COLOR
            self.inventory_tab.background_color = TAB_INACTIVE_COLOR
            self.inventory_tab.color = TEXT_COLOR
            
        except Exception as e:
            logging.error(f"Error switching to master: {e}")

    def logout(self, instance=None):
        """Logout and return to login screen"""
        try:
            self.current_user = None
            self.show_login_screen()
        except Exception as e:
            logging.error(f"Error during logout: {e}")

    def on_pause(self):
        """Handle app pause (Android lifecycle)"""
        logging.info("App paused")
        return True

    def on_resume(self):
        """Handle app resume (Android lifecycle)"""
        logging.info("App resumed")


def run_cli_mode():
    """Run the app in CLI mode when GUI is not available"""
    print("\n" + "="*50)
    print("INVENTARIO APP - CLI MODE CON FIREBASE")
    print("="*50)
    print("GUI mode failed to start. Running in CLI mode.")
    print("This mode provides basic inventory database operations with Firebase sync.\n")
    
    # Initialize core components
    db_manager = DatabaseManager()
    file_manager = FileManager()
    
    print("✅ Database initialized successfully")
    print("✅ File manager initialized successfully")
    
    # Check Firebase
    if HAS_FIREBASE:
        print("✅ Firebase SDK available")
    else:
        print("❌ Firebase SDK not available - offline only")
    
    # Show basic statistics
    try:
        stats = db_manager.get_statistics()
        print(f"\n📊 Current Statistics:")
        print(f"   Total records: {stats.get('total_records', 0)}")
        print(f"   Total items counted: {stats.get('total_quantity', 0)}")
        print(f"   Unique products: {stats.get('unique_products', 0)}")
        print(f"   Last record: {stats.get('last_record_date', 'None')}")
        print(f"   Pending sync: {db_manager.get_pending_sync_count()}")
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    
    # Show recent records
    try:
        records = db_manager.get_last_records(5)
        if records:
            print(f"\n📋 Last 5 records:")
            for record in records:
                sync_status = "✅" if len(record) > 6 and record[6] else "⏳"
                print(f"   🏷️  {record[1]} | {record[2]} | Qty: {record[3]} | {record[4]} | {record[5]} | {sync_status}")
        else:
            print("\n📋 No records found in database")
    except Exception as e:
        print(f"❌ Error getting records: {e}")
    
    print(f"\n📁 Data directory: {android_utils.get_data_directory()}")
    print(f"📄 Database file: {db_manager.db_path}")
    
    print("\nCLI mode is running successfully!")
    print("The database and file operations are working with Firebase sync support.")
    print("For full functionality, use this app on Android or desktop with GUI support.")
    print("\nPress Ctrl+C to exit.")
    
    # Keep the app running so logs can be monitored
    try:
        import time
        while True:
            time.sleep(10)
            logging.info("CLI mode running - database accessible with Firebase sync")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        logging.info("CLI mode stopped by user")

if __name__ == '__main__':
    try:
        InventoryApp().run()
    except Exception as e:
        error_message = str(e).lower()
        if 'window' in error_message or 'display' in error_message or 'glx' in error_message:
            logging.info("GUI mode failed, starting CLI mode...")
            print("GUI initialization failed. Starting CLI mode...")
            run_cli_mode()
        else:
            logging.error(f"Critical error starting app: {e}")
            logging.error(traceback.format_exc())
            raise
