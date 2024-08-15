import openai
import faiss
import numpy as np
import pandas as pd
import os
from datetime import datetime
from common.translator_en import Translator_en
from django.conf import settings

class Chatapi_Call:
    def __init__(self, request, user_message, application_id, api_key, parquet_path, faiss_path):
        print('@@@@@ common/chatapi_call.py : def __init__  @@@@@')   

        self.request = request  # Djangoのrequestオブジェクト
        self.user_message = user_message
        self.application_id = application_id
        self.api_key = api_key
        self.parquet_path = parquet_path
        self.faiss_path = faiss_path
        self.parquet_df = self.load_parquet_file()
        self.index = self.load_faiss_index()
        # 会話履歴の初期化
        if 'generated' not in self.request.session:
            self.request.session['generated'] = []
        if 'past' not in self.request.session:
            self.request.session['past'] = []
        # 会話履歴回数の初期化
        if 'conversation_count' not in self.request.session:
            self.request.session['conversation_count'] = 0
        # 履歴制限メッセージ表示フラグの初期化
        if 'show_history_limit_message' not in self.request.session:
            self.request.session['show_history_limit_message'] = False


    # parquet データを読み込む
    def load_parquet_file(self):
        print('@@@@@ common/chatapi_call.py : def load_parquet_file  @@@@@') 
        return pd.read_parquet(self.parquet_path)

    # Faissインデックスを読み込む
    def load_faiss_index(self):
        print('@@@@@ common/chatapi_call.py : load_faiss_index  @@@@@')
        return faiss.read_index(self.faiss_path)


    def call_openai_chat_completion(self):
        print('@@@@@ common/chatapi_call.py : def call_openai_chat_completion  @@@@@')
        # OpenAI APIキーの設定
        openai.api_key = self.api_key

        # 回答に関連する画像格納用エリアをクリア
        image_paths_to_display = []

        # ユーザーとボットの過去の会話履歴を組み合わせる
        conversation_history = ""
        user_history = self.request.session.get('past', [])
        bot_history = self.request.session.get('generated', [])
        for i, (user_msg, bot_msg) in enumerate(zip(user_history, bot_history), start=1):
            conversation_history += (f"(history{i}) User: {user_msg}\n" 
                                    f" Bot: {bot_msg['text']}\n")

        # 事前確認モードの類似性検索でヒットしたデータのindex-noがある場合は、そのindex-noを使用
        if 'faiss_index_no' in self.request.session:
            similar_text_indices = [self.request.session['faiss_index_no']]
        else:
            # まず文章要約で検索
            summary_faiss_path = self.request.session.get('faiss_path', settings.FAISS_INDEX_SUMMARY_PATH)
            similar_text_indices = self.get_similar_texts_and_images(faiss_path=summary_faiss_path)

            # 文章要約で見つからなかった場合、文章テキストで検索
            if not similar_text_indices or similar_text_indices == [None]:
                similar_text_indices = self.get_similar_texts_and_images()

        print("$$$$$$$$ similar_text_indices $$$$$$$$", similar_text_indices)

        # faq_header 変数を初期化
        faq_header = ""

        # 類似性検索でヒットするものがなかった場合の処理
        if not similar_text_indices or similar_text_indices == [None]:
            print("$$$$$$$$ 回答不能（類似性検索ヒットなし） $$$$$$$$")
            if self.request.session.get('_language') == 'en':
                bot_response = (
                    'Sorry, but I dont have any information about the subject of your question\n'
                    'We cant answer your question. If necessary, please contact our support team.\n'
                    '(Tel: 03(6914)8524,  Email : ifusion_support@imprex.co.jp)'
                )
            else:
                bot_response = (
                    '申し訳ありませんが、ご質問頂いた内容についての情報を持ち合わせていませんので\n'
                    'ご回答できません。必要であれば弊社のサポートチームへ連絡をお願い致します。\n'
                    '(Tel: 03(6914)8524,  Email : ifusion_support@imprex.co.jp)'
                )
            # 会話履歴にユーザーメッセージを追加 
            user_history.append(self.user_message)
            self.request.session['past'] = user_history
        else:
            # USERMSGと類似性検索でヒットしたデータのindex-noから
            # 該当のtextデータと画像データ格納場所のPATHを取得する
            for index in similar_text_indices:
                text, Location, image_paths = self.retrieve_text_and_images(index)
                # 会話履歴格納エリアに該当のtextデータを追加する
                conversation_history += " " + text
                # 画像格納用エリアに該当の画像データ格納場所のPATHを追加する
                image_paths_to_display.extend(image_paths)

            # 会話履歴にユーザーメッセージを追加  
            user_history.append(self.user_message)
            self.request.session['past'] = user_history

            # chatgptに回答させたくない場合の対応（学習データの内容をそのままbotの回答とする）
            if self.request.session.get('_language') == 'en':
                if text.startswith("%%Direct Output%%"):
                    # "%%Direct Output%%" を除いたテキストを英語に翻訳
                    text_to_translate = text.replace("%%Direct Output%%", "", 1).strip()
                    translator = Translator_en(self.api_key)
                    bot_response = translator.translate_to_english(text_to_translate)
                else:
                    # chatgpt api direct call
                    bot_response = self.load_conversation_en(self.user_message, conversation_history)
            else:
                if text.startswith("%%Direct Output%%"):
                    # "%%Direct Output%%" を除いたテSストをそのまま使用
                    bot_response = text.replace("%%Direct Output%%", "", 1).strip()
                else:
                    # chatgpt api direct call
                    bot_response = self.load_conversation(self.user_message, conversation_history)

            # APIからの応答をチェック
            if "回答不能" in bot_response:
                print("$$$$$$$$ 回答不能（BOT 回答不能） $$$$$$$$")
                bot_response = (
                    '申し訳ありませんが、ご質問頂いた内容についての情報を持ち合わせていませんので\n'
                    'ご回答できません。必要であれば弊社のサポートチームへ連絡をお願い致します。\n'
                    '(Tel: 03(6914)8524,  Email : ifusion_support@imprex.co.jp)'
                )

            # APIからの応答をチェック
            if "Unable to answer" in bot_response:
                print("$$$$$$$$ 回答不能（BOT Unable to answer） $$$$$$$$")
                bot_response = (
                    'Sorry, but I dont have any information about the subject of your question\n'
                    'We cant answer your question. If necessary, please contact our support team.\n'
                    '(Tel: 03(6914)8524,  Email : ifusion_support@imprex.co.jp)'
                )

            # index-noがfaqの番号帯の場合、どのマニュアルのFAQであるかを表示する
            if 60001 <= similar_text_indices[0] <= 69999:
                faq_header = f"<<{Location} faq>>\n"
                if not bot_response.startswith(faq_header):
                    bot_response = faq_header + bot_response

        # チャットボット側の履歴に追加する内容には、<<{Location} faq>>は含めない
        if faq_header and bot_response.startswith(faq_header):
            # faq_headerを除いたbot_responseを履歴に保存
            history_response = bot_response[len(faq_header):]
        else:
            # faq_headerがない場合はbot_responseをそのまま使用
            history_response = bot_response

        # チャットボット側の履歴に追加する
        bot_history.append({"text": history_response, "images": image_paths_to_display})
        self.request.session['generated'] = bot_history

        # 履歴が10回を超えた場合、最も古い履歴を削除
        print("len(user_history)", len(user_history))
        self.request.session['conversation_count']  += 1
        print("self.request.session['conversation_count']", self.request.session['conversation_count'])
        print("self.request.session['show_history_limit_message']", self.request.session['show_history_limit_message'])
        if len(user_history) >= 11: 
            user_history.pop(0)    # 最も古いユーザー履歴を削除
            bot_history.pop(0)     # 最も古いボット履歴を削除
            # 会話履歴回数が11件目のタイミングにのみ制限メッセージを表示する対応 
            if self.request.session['conversation_count'] == 11 \
                and not self.request.session['show_history_limit_message']:  # = False 
                self.request.session['show_history_limit_message'] = True
            else:
                self.request.session['show_history_limit_message'] = False
        else:
            self.request.session['show_history_limit_message'] = False

        self.request.session['past'] = user_history
        self.request.session['generated'] = bot_history

        # 会話履歴を指定された形式で表示
        print("<<<<<<<<<会話履歴>>>>>>>>>")
        for i, (user_msg, bot_msg) in enumerate(zip(self.request.session['past'], self.request.session['generated']), start=1):
            print(f"{'（１）' if i == 1 else '（２）' if i == 2 else '（３）' if i == 3 else '（４）' if i == 4 else '（５）' if i == 5 else '（６）' if i == 6 else '（７）' if i == 7 else '（８）' if i == 8 else '（９）' if i == 9 else '（１０）'}ユーザー質問{i}回目の内容")
            print(user_msg)
            print(f"{'（１）' if i == 1 else '（２）' if i == 2 else '（３）' if i == 3 else '（４）' if i == 4 else '（５）' if i == 5 else '（６）' if i == 6 else '（７）' if i == 7 else '（８）' if i == 8 else '（９）' if i == 9 else '（１０）'}ＢＯＴ回答内容{i}回目の内容")
            print(bot_msg['text'])
            print("-" * 150)

        # ユーザーからのメッセージをログに記録
        self.log_conversation('aaaaa@bbb.co.jp', 'user', self.user_message)

        # ボットからのレスポンスをログに記録
        self.log_conversation('aaaaa@bbb.co.jp', 'bot', bot_response)

        # bot_responseと画像データのpathを返す
        return bot_response, image_paths_to_display


    # 類似性検索と画像データの特定を行う
    def get_similar_texts_and_images(self, top_k=10, hit_rate_threshold=0.50, faiss_path=None):
        print('@@@@@ common/chatapi_call.py : def get_similar_texts_and_images  @@@@@')
        # ユーザー入力のベクトル化
        user_embedding = self.get_embedding(self.user_message)
        user_embedding_normalized = self.normalize_L2(np.array(user_embedding).reshape(1, -1))
        # 類似性検索を実行
        if faiss_path:
            index = faiss.read_index(faiss_path)
            print("$$$$$$$$ 文章要約を検索 $$$$$$$$")
        else:
            index = self.index
            print("$$$$$$$$ 文章テキストを検索 $$$$$$$$")
        similarity_scores, similar_indices = index.search(user_embedding_normalized, top_k)
        # ヒット率の閾値に基づいて最もスコアが高いテキストのインデックスを返す
        max_score_idx = None
        max_score = hit_rate_threshold
        for score, idx in zip(similarity_scores[0], similar_indices[0]):
            if score > max_score:
                max_score = score
                max_score_idx = idx

        # 最高スコアのテキストのインデックスを返す（存在しない場合はNone）
        return [max_score_idx] if max_score_idx != -1 else []


    # USER入力のベクトル化を行う関数 parquet からデータ取得 
    # text-embedding-3-large  text-embedding-3-medium  text-embedding-3-small
    def get_embedding(self, text, model="text-embedding-3-large"):
        print('@@@@@ common/chatapi_call.py : def get_embedding  @@@@@')

        text = text.replace("\n", " ")
        return openai.embeddings.create(
            input=[text], model=model).data[0].embedding

    # ベクトルの正規化
    def normalize_L2(self, x):
        return x / np.linalg.norm(x, ord=2, axis=1, keepdims=True)


    # テキストと画像パスを取得
    def retrieve_text_and_images(self, index):
        # print('@@@@@ common/chatapi_call.py : def retrieve_text_and_images  @@@@@')

        filtered_df = self.parquet_df[self.parquet_df['index-no'] == index]
        if not filtered_df.empty:
            data = filtered_df.to_dict('records')[0]
            text = data['文章テキスト']
            Location = data['掲載箇所（項番）']
            image_paths = [os.path.join(data['画像path_bot'], data[f'画像{i}']) for i in range(1, int(data['参照画像数']) + 1)]
            return text, Location, image_paths
        else:
            return "", []


    # gpt-4-1106-preview  gpt-3.5-turbo-16k gpt-4-turbo-2024-04-09 gpt-4o
    def createCompletion(self, prompt):
        # print('@@@@@ common/chatapi_call.py : def createCompletion  @@@@@')

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=prompt,
                temperature = 0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(e)
            raise e


    def load_conversation(self, user_message, conversation_history):
        # print('@@@@@ common/chatapi_call.py : def load_conversation  @@@@@')

        history = conversation_history
        system_msg = f"""
        あなたは株式会社インプレスのパッケージ商品の優秀なカスタマーサポート担当です。
        以下の制約条件に従って、株式会社インプレスのお問い合わせ窓口チャット
        ボットとしてユーザーからの最新質問に回答して下さい。
        ---
        # 制約条件:
        - ユーザーからの質問に対して、回答時の参考情報の最新分の内容を変更せずに、そのまま回答文に転記して下さい。
        - 回答内容は、ユーザーからの最新質問に対してのみ回答して下さい。
        - 回答できないと判断した場合は、回答文に「回答不能」とセットして下さい。
        - 回答内容には、回答時の参考情報の中に含まれているユーザーからの質問には回答しないで下さい。
        - 回答は見出し、箇条書き、表などを使って人間が読みやすく表現してください。
        - **ユーザーの質問の言語に関わらず、常に日本語で回答してください。**

        #回答時の参考情報:
        {history}

        # 回答文:
        """

        prompt = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_message}]

        # プロンプトを生成し、Completion APIを使用して回答を生成します
        completion = self.createCompletion(prompt)
        return completion

        #     # 制約条件:
        # - ユーザーからの質問に対して、回答時の参考情報の内容を変更せずに、そのまま回答文に転記して下さい。
        # - 回答内容は、回答時の参考情報の中に含まれている内容からのみ回答文を作成することを絶対条件とする。
        # - 回答内容は、回答時の参考情報の中に含まれている内容を変更や削除して回答することは絶対禁止とする。
        # - 回答内容は、回答時の参考情報の中に含まれていない内容を追加することは絶対禁止とする。
        # - 回答内容は、ユーザーからの最新質問に対してのみ回答して下さい。
        # - 回答できないと判断した場合は、回答文に「回答不能」とセットして下さい。
        # - 回答内容には、回答時の参考情報の中に含まれているユーザーからの質問には回答しないで下さい。
        # - 回答は見出し、箇条書き、表などを使って人間が読みやすく表現してください。
        # - **ユーザーの質問の言語に関わらず、常に日本語で回答してください。**


    def load_conversation_en(self, user_message, conversation_history):
        # print('@@@@@ common/chatapi_call.py : def load_conversation_en  @@@@@')

        history = conversation_history
        system_msg = f"""
        You are an excellent customer support representative for Impress Corporation's package products.
        Please answer the latest question from the user as a chat bot for Impress Corporation's inquiry desk,
        following the constraints below. Please provide the response in English.
        ---
        # Constraints:
        - In response to a user's question, please transcribe the most recent information in the <Reference information at the time of response:> section into your answer without making any changes.
        - Your answers should only answer the most recent questions from users.
        - If you determine that you cannot answer, set the response text to "Unable to answer".
        - Do not respond to questions from users that are included in the reference information at the time of response.
        - Express the response in a way that is easy for humans to read, using headings, bullet points, tables, etc.
        - **Always respond in English, regardless of the language of the user's question.**

        # Reference information at the time of response:
        {history}

        # Response text:
        """

        prompt = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_message}]

        # Generate the response using the Completion API
        completion = self.createCompletion(prompt)
        return completion
    
        #     # Constraints:
        # - Please generate answers to user questions based on the reference information provided at the time of answering.
        # - It is an absolute requirement that responses must be created solely from the information contained in the reference information at the time of response.
        # - It is strictly prohibited to change or delete any information contained in the reference information at the time of replying.
        # - It is strictly prohibited to add any content to the answer that is not included in the reference information at the time of answering.
        # - Only respond to the user's latest question.
        # - If you determine that you cannot answer, set the response text to "Unable to answer".
        # - Do not respond to questions from users that are included in the reference information at the time of response.
        # - Express the response in a way that is easy for humans to read, using headings, bullet points, tables, etc.
        # - **Always respond in English, regardless of the language of the user's question.**


    def log_conversation(self, user_email, user_or_bot, message):
        try:
            # ルートディレクトリ直下の 'conversation_logs.csv' へのパスを指定
            # csv_file_path = os.path.join('conversation_logs.csv')
            csv_file_path = '/app/conversation_logs.csv'        # Heroku用の指定
            conversation_count = self.request.session.get('conversation_count', 0)
            print(f"CSV file path: {csv_file_path}")            # ログ出力を追加 temp
            print(f"Conversation count: {conversation_count}")  # ログ出力を追加 temp
            # データフレームを作成
            df = pd.DataFrame({
                '日時': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'ユーザーメールアドレス': [user_email],
                'ユーザーボット識別': [user_or_bot],
                '会話回数': [conversation_count],
                'メッセージ内容': [message]
            })
            print(f"DataFrame created: {df}")                   # ログ出力を追加 temp

            # CSVファイルに追記（ファイルが存在しない場合は新規作成）
            # utf-8-sig エンコーディングを指定
            df.to_csv(csv_file_path, mode='a', index=False, header=not os.path.exists(csv_file_path), encoding='utf-8-sig')
            print(f"Logged to {csv_file_path}")  # ログ出力を追加 temp
        except Exception as e:
            print(f"Error logging conversation: {e}")  # エラーログを追加

