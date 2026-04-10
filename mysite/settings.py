"""
Django settings for mysite project.
"""

import os
from pathlib import Path

# BASE DIRECTORY

BASE_DIR = Path(**file**).resolve().parent.parent

# ================================

# SECURITY SETTINGS

# ================================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'unsafe-secret-key')

# Turn OFF in production (set env variable in Render)

DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv(
'DJANGO_ALLOWED_HOSTS',
'localhost,127.0.0.1,major-project-ilap.onrender.com'
).split(',')

# ================================

# APPLICATIONS

# ================================

INSTALLED_APPS = [
'homepage',
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',
]

# ================================

# MIDDLEWARE

# ================================

MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',

```
# ✅ Required for static files in production (Render)
'whitenoise.middleware.WhiteNoiseMiddleware',

'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware',
```

]

# ================================

# URLS & WSGI

# ================================

ROOT_URLCONF = 'mysite.urls'
WSGI_APPLICATION = 'mysite.wsgi.application'

# ================================

# TEMPLATES

# ================================

TEMPLATES = [
{
'BACKEND': 'django.template.backends.django.DjangoTemplates',
'DIRS': [BASE_DIR / "templates"],
'APP_DIRS': True,
'OPTIONS': {
'context_processors': [
'django.template.context_processors.debug',
'django.template.context_processors.request',
'django.contrib.auth.context_processors.auth',
'django.contrib.messages.context_processors.messages',
],
},
},
]

# ================================

# DATABASE (SQLite - simple setup)

# ================================

DATABASES = {
'default': {
'ENGINE': 'django.db.backends.sqlite3',
'NAME': BASE_DIR / "db.sqlite3",
}
}

# ================================

# PASSWORD VALIDATION

# ================================

AUTH_PASSWORD_VALIDATORS = [
{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ================================

# INTERNATIONALIZATION

# ================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

# ================================

# STATIC FILES CONFIG

# ================================

STATIC_URL = '/static/'

# Development static folder

STATICFILES_DIRS = [
BASE_DIR / "assets",
]

# Production static folder

STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise for serving static files

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ================================

# DEFAULT PRIMARY KEY

# ================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ================================

# SESSION SETTINGS

# ================================

SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
