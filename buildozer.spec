[app]

# (str) Title of your application
title = InventarioPro

# (str) Package name
package.name = inventariopro

# (str) Package domain (needed for android/ios packaging)
package.domain = org.inventario.pro

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt,md

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .github, __pycache__, .git, .replit, .buildozer, buildozer_env

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,requests,openpyxl,plyer

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# (list) Android application meta-data to set (key=value format)
android.meta_data = 

# (list) Android library project to add (will be added in the
# project.properties automatically.)
android.library_references = 

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package, or any package from Kotlin source.
# android.enable_androidx requires android.api >= 28
android.enable_androidx = True

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Python Service
# android.service_main_class = org.kivy.android.PythonService

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# In past, was `android.arch` as we weren't supporting builds for multiple archs at the same time.
# android.arch = armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for Android Auto Backup (Android API >=23)
# android.backup_rules = 

# (str) If you need to insert variables into your AndroidManifest.xml file,
# you can do so with the manifest_placeholders property.
# This property allows to tag placeholders in your AndroidManifest.xml with $TAG$
# android.manifest_placeholders = 

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1