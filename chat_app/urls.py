from django.urls import path
from . import views

print('@@@@@ chat_app/urls.py  @@@@@')   

urlpatterns = [
    path('set_language/', views.set_language, name='set_language'),      # 言語設定用のビュー
    path('ask_first/', views.ask_first, name='ask_first'),               # 初回の質問用のビュー
    path('chat_first/', views.chat_first_view, name='chat_first_view'),  # 初回チャットビュー
    path('ask/', views.ask, name='ask'),                                 # 通常の質問用のビュー
    path('chat/', views.chat_view, name='chat_view'),                    # 通常チャットビュー
    path('clear_history/', views.clear_history, name='clear_history'),   # 履歴クリア
    path('end_chatbot/', views.end_chatbot, name='end_chatbot'),         # チャットボット終了
    # 以下は、chat_first.htmlからリダイレクトされた処理を受けるためのビュー
    path('submit_winchange_responses/', views.submit_winchange_responses, name='submit_winchange_responses'), 
    path('submit_faisssearch_responses/', views.submit_faisssearch_responses, name='submit_faisssearch_responses'), 
    path('submit_selected_responses/', views.submit_selected_responses, name='submit_selected_responses'), 
]