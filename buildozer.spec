[app]

title = GN Algo Matrix
package.name = gnalgomatrix
package.domain = org.neeraj
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,requests,plyer
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.private_storage = True
android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE
android.archs = arm64-v8a
android.accept_sdk_license = True
services = gnalgo:service.py

[buildozer]
log_level = 0
bin_dir = bin
