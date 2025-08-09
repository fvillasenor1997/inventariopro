[app]

title = InventarioPro
package.name = inventariopro
package.domain = com.inventario.pro

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,md
source.exclude_dirs = tests, bin, .github, __pycache__, .git, .replit, .buildozer, buildozer_env

version = 1.0

# Simplified requirements compatible with Android
requirements = python3,kivy==2.3.0,requests,openpyxl,plyer,cryptography

orientation = portrait

# Android specific - matching GitHub Actions versions
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,CAMERA
android.enable_androidx = True
android.archs = arm64-v8a, armeabi-v7a
android.ndk = 25.2.9519653
android.sdk = 33
android.api = 33
android.minapi = 21
android.accept_sdk_license = True

# python-for-android options
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
# bin_dir = ./bin