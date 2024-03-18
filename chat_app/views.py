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


@csrf_exempt
def ask(request):
    authenticate_and_get_openai_key(request)
    openai.api_key = request.session["openai_api_key"]

    print('@@@@@ views.py : def ask @@@@@')   
    user_message = request.POST.get('message') 
    conversation = request.session.get('conversation', [])     # これまでの会話をセッションから取得
    conversation.append(user_message)     # ユーザーのメッセージを会話に追加
    prompt = " ".join(conversation)     # コンテキストとしてプロンプトを作成
    # gpt-4-1106-preview  gpt-3.5-turbo
    response = openai.ChatCompletion.create(
      model="gpt-4-1106-preview",
      messages=[
          {
            "role": "system",
            "content": "To improve the readability of responses to users, responses should follow these constraints: Add line breaks to facilitate easier reading. If a concise answer is requested, summarize the response without omitting crucial information. For detailed answers, adhere to the basic format for answer composition, where 'XXXXXX' sections summarize the response content, and 'YYYYYY' sections provide a detailed, itemized explanation. 【Basic Format of Answer】 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXXXX\n1. YYYYYYYYYYYYYYYY\n  (1) YYYYYYYYYYYYYY\n      ① YYYYYYYYYYYYYY\n      ② YYYYYYYYYYYYYY\n          1) YYYYYYYYYYYYYY\n          2) YYYYYYYYYYYYYY\n  (2) YYYYYYYYYYYYYY\n      ① YYYYYYYYYYYYYY\n      ② YYYYYYYYYYYYYY\n2. YYYYYYYYYYYYYYYY\nThe pattern continues in this manner."
          },
          {"role": "user", "content": prompt}
      ]
    )
    bot_response = response['choices'][0]['message']['content'].strip()     # Botの応答を会話に追加    # Botの応答を会話に追加
    conversation.append(bot_response)
    print('@@@@@ views.py conversation @@@@@', conversation)
    request.session['conversation'] = conversation     # 更新された会話をセッションに保存
    return JsonResponse({'message': bot_response})


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


@csrf_exempt
def clear_history(request):
    print('@@@@@ views.py : def clear_history @@@@@')
    if 'conversation' in request.session:
        del request.session['conversation']
    if 'openai_api_key' in request.session:
       del request.session['openai_api_key']
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
        api_url = "https://fastapi-impapikey.onrender.com/verify-authentication-key"
        print('@@@@@ views.py : api call start @@@@@')
        response = requests.post(api_url, json={"client_key": authentication_key})
        print('@@@@@ views.py : api call end @@@@@')
        if response.status_code == 200:
            openai_api_key = response.json()["decrypted_api_key"]
            # openai.api_key = openai_api_key
            request.session["openai_api_key"] = openai_api_key  # DjangoのセッションにAPIキーを保存
        else:
            print("認証に失敗しました。")  # 仮のエラーハンドリング        
        return HttpResponse("OpenAI key is: " + request.session['openai_api_key'])