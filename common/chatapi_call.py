import openai
import faiss
import numpy as np
import pandas as pd
import os
from datetime import datetime

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
        print('@@@@@ self.parquet_path  @@@@@', self.parquet_path)
        return pd.read_parquet(self.parquet_path)

    # Faissインデックスを読み込む
    def load_faiss_index(self):
        print('@@@@@ common/chatapi_call.py : load_faiss_index  @@@@@')
        print('@@@@@ self.faiss_path  @@@@@', self.faiss_path)
        return faiss.read_index(self.faiss_path)


    def call_openai_chat_completion(self):
        print('@@@@@ common/chatapi_call.py : def call_openai_chat_completion  @@@@@')
        # OpenAI APIキーの設定
        openai.api_key = self.api_key

        # 回答に関連する画像格納用エリアをクリア
        image_paths_to_display = []

        # ユーザーとボットの過去の会話履歴を組み合わせる
        conversation_history = ""

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
            similar_text_indices = self.get_similar_texts_and_images()
        print("$$$$$$$$ similar_text_indices $$$$$$$$", similar_text_indices)

        # USERMSGと類似性検索でヒットしたデータのindex-noから
        # 該当のtextデータと画像データ格納場所のPATHを取得する
        if similar_text_indices:
            for index in similar_text_indices:
                text, image_paths = self.retrieve_text_and_images(index)
                # 会話履歴格納エリアに該当のtextデータを追加する
                conversation_history += " " + text
                # 画像格納用エリアに該当の画像データ格納場所のPATHを追加する
                image_paths_to_display.extend(image_paths)

        # 会話履歴にユーザーメッセージを追加  
        user_history.append(self.user_message)
        self.request.session['past'] = user_history

        # chatgpt api direct call
        print("self.user_message", self.user_message)
        print("conversation_history", conversation_history)
        bot_response = self.load_conversation(self.user_message, conversation_history)

        # APIからの応答をチェック
        if "回答不能" in bot_response:
            bot_response = (
            '申し訳ありませんが、ご質問頂いた内容についての情報を持ち合わせていませんので\n'
            'ご回答できません。必要であれば弊社のサポートチームへ連絡をお願い致します。\n'
            '(Tel:xxxxxx, Email:xxxxx@imprex.co.jp)'
        )

        # チャットボット側の履歴に追加する
        bot_history.append({"text": bot_response, "images": image_paths_to_display})
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

        print("self.request.session['past']", self.request.session['past'])
        print("self.request.session['generated']", self.request.session['generated'])

        # ユーザーからのメッセージをログに記録
        self.log_conversation('aaaaa@bbb.co.jp', 'user', self.user_message)

        # ボットからのレスポンスをログに記録
        self.log_conversation('aaaaa@bbb.co.jp', 'bot', bot_response)

        # bot_responseと画像データのpathを返す
        return bot_response, image_paths_to_display    


    # 類似性検索と画像データの特定を行う
    def get_similar_texts_and_images(self, top_k=10, hit_rate_threshold=0.50):
        print('@@@@@ common/chatapi_call.py : def get_similar_texts_and_images  @@@@@')
        # ユーザー入力のベクトル化
        user_embedding = self.get_embedding(self.user_message)
        user_embedding_normalized = self.normalize_L2(np.array(user_embedding).reshape(1, -1))
        # 類似性検索を実行
        similarity_scores, similar_indices = self.index.search(user_embedding_normalized, top_k)
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
        print('@@@@@ common/chatapi_call.py : def retrieve_text_and_images  @@@@@')

        filtered_df = self.parquet_df[self.parquet_df['index-no'] == index]
        if not filtered_df.empty:
            data = filtered_df.to_dict('records')[0]
            text = data['文章テキスト']
            image_paths = [os.path.join(data['画像path_bot'], data[f'画像{i}']) for i in range(1, data['参照画像数'] + 1)]
            return text, image_paths
        else:
            return "", []


    # gpt-4-1106-preview  gpt-3.5-turbo-16k gpt-4-turbo-2024-04-09 gpt-4o
    def createCompletion(self, prompt):
        print('@@@@@ common/chatapi_call.py : def createCompletion  @@@@@')

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
        print('@@@@@ common/chatapi_call.py : def load_conversation  @@@@@')

        history = conversation_history
        system_msg = f"""
        あなたは株式会社インプレスのパッケージ商品の優秀なカスタマーサポート担当です。
        以下の制約条件に従って、株式会社インプレスのお問い合わせ窓口チャット
        ボットとしてユーザーからの最新質問に回答して下さい。
        ---
        # 制約条件:
        - ユーザーからの質問に対して、回答時の参考情報を参考にして回答文を生成して下さい。
        - 回答内容は、ユーザーからの最新質問に対してのみ回答して下さい。
        - 回答できないと判断した場合は、回答文は「回答不能」とセットして下さい。
        - 回答内容には、回答時の参考情報の中に含まれているユーザーからの質問には回答しないで下さい。
        - 回答は見出し、箇条書き、表などを使って人間が読みやすく表現してください。

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
    
    
    def log_conversation(self, user_email, user_or_bot, message):
        print('@@@@@ common/chatapi_call.py : def log_conversation  @@@@@')
        
        # ルートディレクトリ直下の 'conversation_logs.csv' へのパスを指定
        csv_file_path = os.path.join('conversation_logs.csv')
        conversation_count = self.request.session.get('conversation_count', 0)
        # データフレームを作成
        df = pd.DataFrame({
            '日時': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'ユーザーメールアドレス': [user_email],
            'ユーザーボット識別': [user_or_bot],
            '会話回数': [conversation_count],
            'メッセージ内容': [message]
        })
        # CSVファイルに追記（ファイルが存在しない場合は新規作成）
        # utf-8-sig エンコーディングを指定
        df.to_csv(csv_file_path, mode='a', index=False, header=not os.path.exists(csv_file_path), encoding='utf-8-sig')


