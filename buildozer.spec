[app]
title = AgriSense
package.name = agrisense
package.domain = lk.vectamind

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,sql
version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,sqlalchemy,pymysql,bcrypt,matplotlib,kivy_garden.matplotlib,python-dotenv,pandas,numpy,pillow

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

# ------------------------------------------------------------------
# NOTE: A phone cannot reach "localhost" MySQL. Before building the
# APK, point DB_HOST in .env to your server's real IP/hostname (a
# cloud MySQL instance, or your PC's LAN IP while testing on the
# same WiFi), and make sure port 3306 is reachable from the phone.
# ------------------------------------------------------------------
