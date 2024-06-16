"""
WSGI config for django_chatbot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

import logging  # ロギングモジュールをインポート

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_chatbot.settings')

# Heroku固有設定 start    標準出力にログを出力する設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Heroku固有設定 end

# ロガーの設定

logger = logging.getLogger('django')

# アプリケーション起動時にINFOレベルのログを出力

logger.info('<<<<<< iFUSION-Chatbot start >>>>>>')

application = get_wsgi_application()

