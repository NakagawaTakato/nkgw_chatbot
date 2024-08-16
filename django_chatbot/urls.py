"""
URL configuration for django_chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language
#from chat_app.views import chat_view
from chat_app.views import chat_first_view
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from django.conf.urls.static import static

print('@@@@@ django_chatbot/urls.py  @@@@@')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('set_language/', set_language, name='set_language'),
    path('chat_app/', include('chat_app.urls')),       # chat_appのurls.pyを参照
    path('', chat_first_view, name='home'),            # ルートURLでchat_first_viewを呼び出す
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('icon/favicon.ico')), name='favicon'),
]

# 画像ファイルへのアクセスを設定
urlpatterns += static('/chat_app/chat/common/imagefile/', document_root=settings.IMAGE_FILE_PATH)

# メディアファイルへのアクセスを設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)