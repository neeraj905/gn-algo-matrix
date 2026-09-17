[app]

# Title of your application
title = GN Algo Matrix

# Package name
package.name = gnalgomatrix

# Package domain (needed for android packaging)
package.domain = org.neeraj

# Source files to include (let it include all Python and configuration files)
source.include_exts = py,png,jpg,kv,atlas,json,csv,txt

# List of source files to include (let it include your main code/entry point)
source.include_patterns = assets/*,*.py

# Icon of the application
#icon.filename = %(source.dir)s/icon.png

# Supported orientation (landscape, portrait or all)
orientation = portrait

# List of requirements your app needs
# Add python3, kivy, and any other trading/math libraries your project uses
requirements = python3,kivy,requests,urllib3,certifi,idna,charset-normalizer

# Custom blacklist-the-package (if any)
#exclude_patterns = license,images/*/*.jpg

# Indicate if the application should be fullscreen or not
fullscreen = 0

# Android specific

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --public storage (False)
android.private_storage = True

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (list) Presplash background color
android.presplash_color = #000000

# (list) Supported architectures
android.archs = arm64-v8a, armeabi-v7a

# (str) pyjnius implementation
#pyjnius = master

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifact storage, absolute or relative to the spec file
build_dir = .buildozer

# (str) Path to build output (APK, AAB, etc.)
bin_dir = bin
