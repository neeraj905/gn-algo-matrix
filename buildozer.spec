[app]
title = GN Algo Matrix
package.name = gnalgomatrix
package.domain = org.neeraj
source.include_exts = py,png,jpg,kv,atlas,json,csv,txt
source.include_patterns = assets/*,*.py
orientation = portrait
requirements = python3,kivy,requests
fullscreen = 0
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.private_storage = True
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
bin_dir = bin
