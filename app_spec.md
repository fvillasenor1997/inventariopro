
# Inventario App - Especificación Técnica

## Descripción General
Aplicación de inventario con soporte para Firebase, funcionamiento offline/online, sincronización en tiempo real y control de auditores/contadores.

## Características Principales

### 🔐 Autenticación y Seguridad
- **Login Usuario/Contraseña**: Sistema de autenticación local y Firebase
- **Configuración Firebase**: Pantalla inicial para configurar credenciales Firebase
- **Control de Sesión**: Manejo seguro de tokens de autenticación
- **Auditoría**: Registro completo de todas las operaciones

### 🌐 Conectividad Híbrida
- **Modo Online**: Sincronización automática con Firebase Firestore
- **Modo Offline**: Funcionamiento completo sin conexión a internet
- **Sincronización Automática**: Sincronización cada 30 segundos cuando hay conexión
- **Sincronización Manual**: Botón para forzar sincronización inmediata
- **Cola de Sincronización**: Los cambios offline se sincronizan automáticamente al recuperar conexión

### 📊 Gestión de Inventario
- **Escaneo de Códigos**: Soporte para códigos de barras con entrada por teclado
- **Master de Artículos**: Carga desde Excel (xlsx, xls)
- **Conteo por Locaciones**: Organización por ubicaciones
- **Control de Auditores**: Seguimiento de quién realizó cada conteo
- **Búsqueda Avanzada**: Filtros por código, descripción, auditor, locación
- **Edición de Registros**: Modificación y eliminación de conteos existentes

### 💾 Persistencia de Datos
- **Base de Datos Local**: SQLite para almacenamiento offline
- **Backup/Restore**: Exportación e importación de datos en JSON
- **Sincronización Bidireccional**: Conflictos resueltos por timestamp
- **IDs Únicos**: Sistema dual local/Firebase para evitar duplicados

### 🎨 Interfaz de Usuario
- **Diseño Responsive**: Adaptable a diferentes tamaños de pantalla
- **Alto Contraste**: Paleta de colores optimizada para visibilidad
- **Indicadores de Estado**: Visualización clara del estado de sincronización
- **Navegación por Pestañas**: Conteo y Master en pestañas separadas
- **Feedback Visual**: Confirmaciones y alertas claras

## Arquitectura Técnica

### Tecnologías Utilizadas
- **Frontend**: Kivy (Python) para multiplataforma
- **Backend Local**: SQLite para persistencia offline
- **Backend Remoto**: Firebase Firestore para sincronización
- **Autenticación**: Firebase Auth
- **Archivos**: openpyxl para Excel, plyer para sistema de archivos

### Estructura de Módulos
```
├── main.py                 # Aplicación principal
├── firebase_manager.py     # Gestión Firebase
├── database_manager.py     # Base de datos SQLite
├── android_utils.py        # Utilidades Android
├── file_manager.py         # Gestión de archivos
├── logging_config.py       # Configuración de logging
└── requirements.txt        # Dependencias
```

### Modelo de Datos

#### Tabla Inventory
```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    codigo_barras TEXT NOT NULL,
    descripcion TEXT,
    cantidad INTEGER NOT NULL,
    auditor TEXT,
    locacion TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    local_id TEXT UNIQUE,           -- ID único local
    firebase_id TEXT,               -- ID de Firebase
    sync_status INTEGER DEFAULT 0,  -- 0=pendiente, 1=sincronizado
    created_by TEXT,                -- Usuario que creó el registro
    last_modified DATETIME
);
```

#### Colección Firebase (Firestore)
```javascript
{
  codigo_barras: string,
  descripcion: string,
  cantidad: number,
  auditor: string,
  locacion: string,
  timestamp: timestamp,
  user_id: string,
  local_id: string,
  sync_status: boolean
}
```

### Flujo de Sincronización

#### Nuevo Registro
1. Se crea localmente con `sync_status = 0`
2. Se genera `local_id` único (UUID)
3. Se intenta sincronización inmediata si hay conexión
4. Si no hay conexión, queda pendiente en cola

#### Sincronización Automática
1. Cada 30 segundos se ejecuta proceso de sincronización
2. Se obtienen registros con `sync_status = 0`
3. Se envían a Firebase Firestore
4. Se marcan como sincronizados localmente
5. Se obtienen actualizaciones remotas desde último sync

#### Resolución de Conflictos
- Por timestamp: el más reciente prevalece
- Por usuario: se mantiene registro de quién modificó qué
- Logs de auditoría para rastrear cambios

## Configuración Firebase

### Configuración Requerida
```json
{
  "projectId": "tu-proyecto-firebase",
  "apiKey": "AIzaSy...",
  "authDomain": "tu-proyecto.firebaseapp.com",
  "databaseURL": "https://tu-proyecto-default-rtdb.firebaseio.com/",
  "storageBucket": "tu-proyecto.appspot.com"
}
```

### Reglas de Firestore
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /inventory/{document} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### Reglas de Authentication
```javascript
// Permitir registro y login con email/password
// Configurar en Firebase Console
```

## Características de Seguridad

### Autenticación Local
- Passwords hasheados con SHA-256
- Usuario admin por defecto (admin/admin)
- Tokens de sesión para Firebase

### Auditoría
- Log completo de todas las operaciones
- Timestamp de cada acción
- Usuario responsable de cada cambio
- Historial de sincronizaciones

### Validaciones
- Códigos de barras obligatorios
- Cantidades numéricas válidas
- Tokens de Firebase válidos
- Timeouts de conexión configurables

## Manejo de Errores

### Errores de Conexión
- Fallback automático a modo offline
- Reintentos automáticos con backoff exponencial
- Notificaciones claras al usuario

### Errores de Datos
- Validación en frontend y backend
- Rollback automático en caso de error
- Logs detallados para debugging

### Errores de Sincronización
- Cola persistente de operaciones pendientes
- Resolución automática de conflictos
- Alertas para conflictos no resolubles

## Instalación y Despliegue

### Dependencias Python
```
kivy>=2.1.0
firebase-admin>=6.0.0
requests>=2.28.0
openpyxl>=3.0.0
plyer>=2.1.0
```

### Configuración Android
- Permisos de almacenamiento
- Permisos de red
- Configuración de AndroidManifest.xml

### Variables de Entorno
```
FIREBASE_CONFIG_PATH=path/to/firebase/config.json
DATABASE_PATH=path/to/database.db
LOG_LEVEL=INFO
```

## Testing

### Unit Tests
- Tests de sincronización
- Tests de base de datos
- Tests de Firebase manager
- Tests de validaciones

### Integration Tests
- Tests end-to-end de flujos principales
- Tests de conectividad
- Tests de recuperación de errores

### Performance Tests
- Tests de carga con múltiples registros
- Tests de sincronización masiva
- Tests de memoria y CPU

## Roadmap

### Versión 1.0 (Actual)
- ✅ Funcionalidad básica de inventario
- ✅ Integración Firebase
- ✅ Sincronización offline/online
- ✅ Autenticación básica

### Versión 1.1 (Próxima)
- 📱 Soporte mejorado para tablets
- 🔄 Sincronización incremental
- 📊 Reportes básicos
- 🔍 Búsqueda mejorada

### Versión 2.0 (Futuro)
- 📸 Captura de imágenes
- 📈 Dashboard analytics
- 👥 Gestión de equipos
- 🌍 Múltiples idiomas

## Soporte y Mantenimiento

### Logs
- Logs rotativos por fecha
- Diferentes niveles (DEBUG, INFO, WARNING, ERROR)
- Logs de sincronización separados

### Monitoreo
- Estado de sincronización en tiempo real
- Métricas de performance
- Alertas de errores críticos

### Backup
- Backup automático diario
- Exportación manual a JSON/Excel
- Restauración selectiva de datos
