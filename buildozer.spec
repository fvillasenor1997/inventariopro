[app]

title = InventarioPro
package.name = inventariopro
package.domain = com.inventario.pro

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,md
source.exclude_dirs = tests, bin, .github, __pycache__, .git, .replit

version = 1.0

# Mantener dependencias necesarias y evitar firebase-admin (usamos REST con requests)
requirements = python3,kivy==2.3.0,requests,openpyxl,plyer,pyjnius

orientation = portrait

# Android specific
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,CAMERA
android.enable_androidx = True
android.archs = arm64-v8a, armeabi-v7a
android.api = 30
android.minapi = 21

# python-for-android options
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
# bin_dir = ./bin