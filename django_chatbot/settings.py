"""
Django settings for django_chatbot project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os 
import django_on_heroku    # heroku 固有の設定
import dj_database_url     # heroku 固有の設定

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-joxqtmil(o$(+bm15t1vnro9td3wgbig0^+!1ms68aq$scprqn'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = []
ALLOWED_HOSTS = ['*']    # ngrok,herokuの設定　

# CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app']  # ngrokの固有設定

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chat_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

ROOT_URLCONF = 'django_chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  
            ],
        },
    },
]

WSGI_APPLICATION = 'django_chatbot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True
USE_L10N = True

USE_TZ = True

# 使用する言語
LANGUAGES = [
    ('en', 'English'),
    ('ja', 'Japanese'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# STATIC_URL = '/static/'
# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"),]

STATIC_URL = 'static/'                   # heroku 固有の設定
STATIC_DIR = BASE_DIR / "static"         # heroku 固有の設定
STATICFILES_DIRS = [STATIC_DIR,]

# 画像ファイルが保存されているディレクトリへのパスを追加
IMAGE_FILE_PATH = os.path.join(BASE_DIR, 'common', 'imagefile')

django_on_heroku.settings(locals())      # heroku 固有の設定

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# common/dataディレクトリ内のファイルへのパス
PARQUET_FILE_PATH = os.path.join(BASE_DIR, 'common', 'data', 'output_data_all.parquet')
FAISS_INDEX_PATH = os.path.join(BASE_DIR, 'common', 'data', 'faiss_index_all.idx')
FAISS_INDEX_SUMMARY_PATH = os.path.join(BASE_DIR, 'common', 'data', 'faiss_index_all_summary.idx')

# Heroku 固有設定
# Herokuのファイルシステムは一時的であり、アプリケーションの再起動やデプロイのたびにリセットされるため、
# ファイルにログを保存するのは適していません。具体的には、以下の点が問題となります。
# 1. 一時的なファイルシステム: Herokuでは、ファイルシステムが一時的であり、アプリケーションの再起動やデプロイのたびにリセット
# 　　されるため、ファイルにログを保存するのは適していません。具体的には、以下の点が問題となります：
# 2. ログの保存場所: Herokuでは、ログは標準出力（コンソール）に出力するのが一般的です。
# 　　これにより、Herokuのログ機能を通じてログを確認できます。
# 上記の理由から、Herokuではファイルにログを保存するのではなく、標準出力（コンソール）に出力するように設定します。
#  
# ロギング　（Heroku用）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # ロガーの設定
    'loggers': {
        # Djangoが利用するロガー
        'django': {
            'handlers': ['console'], 
            'level': 'INFO',
        },
        # diaryアプリケーションが利用するロガー
        'diary': {
            'handlers': ['console'], 
            'level': 'INFO',
        },
    },

    # ハンドラの設定
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'prod',
        },
    },

    # フォーマッタの設定
    'formatters': {
        'prod': {
            'format': '\t'.join([
                '%(asctime)s',
                '[%(levelname)s]',
                '%(pathname)s(Line:%(lineno)d)',
                '%(message)s'
            ])
        },
    }
}