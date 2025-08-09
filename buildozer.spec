[app]

title = InventarioPro
package.name = inventariopro
package.domain = com.inventario.pro

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,md
source.exclude_dirs = tests, bin, .github, __pycache__, .git, .replit, .buildozer, buildozer_env

version = 1.0

# Minimal requirements for testing
requirements = python3,kivy

orientation = portrait

# Android specific - minimal configuration
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.archs = arm64-v8a

[buildozer]
log_level = 2