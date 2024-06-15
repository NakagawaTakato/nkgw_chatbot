from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
from django.utils import translation
from chat_app.forms import LanguageForm
from django.shortcuts import redirect
import os
from dotenv import load_dotenv
import boto3
import json
from django.http import HttpResponse
import requests
from django.views.decorators.http import require_http_methods
# chatapi_call.py から クラスをインポート
from common.chatapi_call import Chatapi_Call
# chatapi_call_first.py から クラスをインポート
from common.chatapi_call_first import Chatapi_Call_first
from django.conf import settings


# 初回のUSER質問を受け付ける処理（回答ターゲットをある程度特定させるための処理）
def ask_first(request):
    print('@@@@@ views.py : def ask_first @@@@@')
    authenticate_and_get_openai_key(request)
    openai.api_key = request.session["openai_api_key"]
    user_message = request.POST.get('message') 
    application_id = "django_chatapp1"
    # parquet_path(全学習データ)とfaiss_path(全学習データ要約分）を
    # settingsから取得するように修正
    parquet_path = settings.PARQUET_FILE_PATH
    faiss_path   = settings.FAISS_INDEX_SUMMARY_PATH
    # Chatapi_Call_firstクラスをインスタンス化
    chatapi_call_first = Chatapi_Call_first(request, user_message, application_id,
                                            openai.api_key, parquet_path, faiss_path)
    # Chatapi_Call_firstクラスにより、ボットの複数回答を取得する
    bot_responses = chatapi_call_first.call_openai_chat_completion()
    print('@@@@@ views.py : bot_responses @@@@@', bot_responses)
    # chat_first.htmlにデータを渡してレンダリング
    return JsonResponse({'responses': bot_responses})


# ユーザーの質問に対してボットが回答する通常処理(フリー会話モード)
def ask(request):
    print('@@@@@ views.py : def ask @@@@@')
    authenticate_and_get_openai_key(request)
    openai.api_key = request.session["openai_api_key"]
    user_message = request.POST.get('message')
    application_id = "django_chatapp2"

    # セッションに 'select_index' が存在する（聞きたいことが指定された）場合
    # 検索対象を絞った学習データを使用する
    if 'select_index' in request.session :
        parquet_path = request.session.get('parquet_path')
        faiss_path = request.session.get('faiss_path')
    else:
        # parquet_path(全学習データ)とfaiss_path(全学習データ)を
        # settingsから取得する
        parquet_path = settings.PARQUET_FILE_PATH
        faiss_path = settings.FAISS_INDEX_PATH

    # Chatapi_Callクラスをインスタンス化
    chatapi_call = Chatapi_Call(request, user_message, application_id,
                                openai.api_key, parquet_path, faiss_path)
    # Chatapi_Callクラスにより、ボットの回答と会話履歴の更新を行う
    bot_response, image_paths_to_display = chatapi_call.call_openai_chat_completion()
    history_limit_message = request.session.get('show_history_limit_message', False) 

    # セッションにchat_first.htmlから連携した文言を設定している
    # Text をクリアする
    if 'selectedText' in request.session:
        del request.session['selectedText']
    if 'faiss_selectedText' in request.session:
        del request.session['faiss_selectedText']

    # セッションにchat_first.htmlから連携した文言を設定している
    # index をクリアする
    if 'select_index' in request.session:
        del request.session['select_index']
    if 'faiss_index_no' in request.session:
        del request.session['faiss_index_no']

    return JsonResponse({
        'message': bot_response,           # ボットからのテキストレスポンス
        'images': image_paths_to_display,  # 画像パスのリスト
        'show_history_limit_message': history_limit_message,  # 会話履歴の制限メッセージの表示フラグ
    })


@require_http_methods(["POST"])
def submit_winchange_responses(request):
    try:
        print('@@@@@ views.py : def submit_winchang_responses @@@@@')
        data = json.loads(request.body)
        index = data.get('index')

        # 選択されたインデックスとテキストに基づいて必要な処理を行う
        print(f"選択されたインデックス: {index}")

        # 応答を返す
        return JsonResponse({'status': 'success', 'message': '選択された回答が正常に処理されました。'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_http_methods(["POST"])
def submit_faisssearch_responses(request):
    try:
        print('@@@@@ views.py : def submit_faisssearch_responses @@@@@')
        data = json.loads(request.body)
        index = data.get('index')
        text = data.get('text') 

        # 選択されたインデックスとテキストに基づいて必要な処理を行う
        print(f"選択されたインデックス: {index}, テキスト: {text}")  

        # Faiss検索用インデックスをセッションに保存
        request.session['faiss_index_no'] = index  

        # テキストをセッションに保存
        request.session['faiss_selectedText'] = text 

        # 応答を返す
        return JsonResponse({'status': 'success', 'message': '選択された回答が正常に処理されました。'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_http_methods(["POST"])
def submit_selected_responses(request):
    try:
        print('@@@@@ views.py : def submit_selected_responses @@@@@')
        data = json.loads(request.body)
        index = data.get('index')
        text = data.get('text')   

        # 選択されたインデックスとテキストに基づいて必要な処理を行う
        print(f"選択されたインデックス: {index}, テキスト: {text}")

        # 聞きたい事インデックスをセッションに保存
        request.session['select_index'] = index  

        # テキストをセッションに保存
        request.session['selectedText'] = text  

        # indexに応じてパスをセッションに設定
        match index:
            case 'sel_etc2_1' | 'sel_etc2_3' | 'sel_etc2_4' | 'sel_etc2_6' | 'sel_etc2_8':
                request.session['parquet_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'output_data_Portal.parquet')
                request.session['faiss_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'faiss_index_Portal.idx')
            case 'sel_etc2_2':
                request.session['parquet_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'output_data_Designer.parquet')
                request.session['faiss_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'faiss_index_Designer.idx')
            case 'sel_etc2_5':
                request.session['parquet_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'output_data_Client.parquet')
                request.session['faiss_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'faiss_index_Client.idx')
            case 'sel_etc2_7':
                request.session['parquet_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'output_data_Next.parquet')
                request.session['faiss_path'] = os.path.join(settings.BASE_DIR, 'common', 'data', 'faiss_index_Next.idx')

        print(f"選択されたparquet_path: {request.session['parquet_path']}, faiss_path: {request.session['faiss_path']}")

        # 応答を返す
        return JsonResponse({'status': 'success', 'message': '選択された回答が正常に処理されました。'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def chat_first_view(request):
    print('@@@@@ views.py : def chat_first_view @@@@@')
    context = {
        'initial_bot_message': (
            '　ご利用ありがとうございます。ご質問に的確にお答えするために、最初にご質問の内容を確認させて頂きます。<br>'
            '　　 まずは、下記の入力欄に質問内容を入力して送信して下さい。<br>'
            '　　 事前確認が不要な場合は、会話モードをフリー会話モードに切り替えて下さい。'
        )
    }
    return render(request, 'chat_first.html', context)


def chat_view(request):
    print('@@@@@ views.py : def chat_view @@@@@')
    return render(request, 'chat.html')


def set_language(request):
    print('@@@@@ views.py : def set_language @@@@@')
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            user_language = form.cleaned_data['language']
            translation.activate(user_language)
            request.session['_language'] = user_language
    return redirect(request.META.get('HTTP_REFERER', '/'))


def clear_history(request):
    print('@@@@@ views.py : def clear_history @@@@@')
    if 'openai_api_key' in request.session:
        del request.session['openai_api_key']
    if 'past' in request.session:
        del request.session['past']
    if 'generated' in request.session:
        del request.session['generated']
    if 'show_history_limit_message' in request.session:
        del request.session['show_history_limit_message']
    if 'conversation_count' in request.session:
        del request.session['conversation_count']
    if 'select_index' in request.session:
        del request.session['select_index']
    if 'selectedText' in request.session:
        del request.session['selectedText']
    if 'parquet_path' in request.session:
        del request.session['parquet_path']
    if 'faiss_path' in request.session:
        del request.session['faiss_path']
    if 'faiss_index_no' in request.session:
        del request.session['faiss_index_no']
    if 'faiss_selectedText' in request.session:
        del request.session['faiss_selectedText']
    return JsonResponse({'status': 'success'})


def authenticate_and_get_openai_key(request):
    print('@@@@@ views.py : def authenticate_and_get_openai_key @@@@@')
    if 'openai_api_key' not in request.session:
        # 環境変数の読み込み
        load_dotenv()
            # 実行環境の判断
        is_aws = os.getenv('AWS_ENV') == 'production'

        # 認証キーの取得
        if is_aws:
            # AWS環境の場合
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId="Authentication_key")
            secret_dict = json.loads(response['SecretString'])
            authentication_key = secret_dict.get("Authentication_key")
            print('%%%%%% secretsmanager value %%%%%%', authentication_key)  # @@@本番デプロイ時にはコメントアウト
        else:
            # ローカル環境の場合
            authentication_key = os.getenv("Authentication_key")
            print('%%%%%% local.env value %%%%%%', authentication_key)       # @@@本番デプロイ時にはコメントアウト

        # APIエンドポイントのURL   @@@本番組込時には適切なURLに変更する
        # FastAPIのエンドポイントを適切に指定する
        # api_url = "https://fastapi-impapikey.onrender.com/verify-authentication-key"   renderのURL 
        api_url = "https://fastapi-keyget-4cdd2eb0f921.herokuapp.com/verify-authentication-key"   # HerokuのURL
        print('@@@@@ views.py : api call start @@@@@')
        response = requests.post(api_url, json={"client_key": authentication_key})
        print('@@@@@ views.py : api call end @@@@@')
        if response.status_code == 200:
            openai_api_key = response.json()["decrypted_api_key"]
            # openai.api_key = openai_api_key
            request.session["openai_api_key"] = openai_api_key  # DjangoのセッションにAPIキーを保存
        else:
            print("認証に失敗しました。")  # 仮のエラーハンドリング
            print("response.status_code: ", response.status_code)  # 仮のエラーハンドリング
        return HttpResponse("OpenAI key is: " + request.session['openai_api_key'])