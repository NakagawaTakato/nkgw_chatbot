from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # これによりset_languageビューへのURLが含まれる
]

urlpatterns += i18n_patterns(
    path('chat_app/', include('chat_app.urls')),  # アプリケーションのURLパターン
    # 必要に応じて他のURLパターンを追加
)
