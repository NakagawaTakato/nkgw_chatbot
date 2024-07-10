import openai
import faiss
import numpy as np
import pandas as pd
import os
from datetime import datetime
from common.chatapi_call import Chatapi_Call
from common.translator_en import Translator_en

class Chatapi_Call_first(Chatapi_Call):
    def __init__(self, request, user_message, application_id, api_key, parquet_path, faiss_path):
        print('@@@@@ common/chatapi_call_first.py : def __init__  @@@@@')   
        super().__init__(request, user_message, application_id, api_key, parquet_path, faiss_path)


    # オーバーライドメソッド
    def call_openai_chat_completion(self):
        print('@@@@@ common/chatapi_call_first.py : def call_openai_chat_completion  @@@@@')
        # OpenAI APIキーの設定
        openai.api_key = self.api_key

        # USERMSGと類似性検索でヒットしたデータのindex-noから
        # 該当のtextデータを取得する
        similar_text_indices = self.get_similar_texts_and_images()
        image_paths_to_display = []  # 画像パスを格納するリストを初期化
        bot_responses = []         # 抽出したテキストを格納するリスト

        for index in similar_text_indices:
            # テキストデータとインデックス番号の取得
            text, index_no = self.retrieve_text(index) 
            if text:  # テキストが存在する場合、抽出したテキストとインデックスをリストに追加
                bot_responses.append({'text': text, 'index_no': index_no}) 

        print('@@@@@ Chatapi_Call_first/bot_responses_before @@@@@', bot_responses)

        # 言語選択が英語の場合に英語に翻訳した内容に置き換える
        print('@@@@@ common/chatapi_call_first.py : def call_openai_chat_completion  @@@@@',self.request.session.get('_language'))
        if self.request.session.get('_language') == 'en':
            translator = Translator_en(self.api_key)
            for response in bot_responses:
                response['text'] = translator.translate_to_english(response['text'])

        print('@@@@@ Chatapi_Call_first/bot_responses_after @@@@@', bot_responses)

        # ユーザーからのメッセージとボットからのレスポンスをログに記録
        self.log_conversation('aaaaa@bbb.co.jp', 'user', self.user_message)
        for response in bot_responses:
            self.log_conversation('aaaaa@bbb.co.jp', 'bot', response)

        # bot_responsesをリスト形式で返す
        return bot_responses 


    def get_similar_texts_and_images(self, top_k=5, hit_rate_threshold=0.50):   #調整必要 0.50  
        print('@@@@@ common/chatapi_call_first.py : def get_similar_texts_and_images  @@@@@')
        # ユーザー入力のベクトル化
        print('@@@@@ self.user_message @@@@@', self.user_message)
        user_embedding = self.get_embedding(self.user_message)
        user_embedding_normalized = self.normalize_L2(np.array(user_embedding).reshape(1, -1))
        # 類似性検索を実行
        similarity_scores, similar_indices = self.index.search(user_embedding_normalized, top_k)
        print('@@@@@ similarity_scores @@@@@', similarity_scores)
        print('@@@@@ similar_indices @@@@@', similar_indices)
        # top_k=5 の指定で抽出されたテキストのインデックスをそのまま返す
        # スコアが hit_rate_threshold 以上のもののみをフィルタリング
        filtered_indices = [idx for score, idx in zip(similarity_scores[0], similar_indices[0]) if score >= hit_rate_threshold]
        print('@@@@@ filtered_indices @@@@@', filtered_indices)
        # フィルタリングされたインデックスを返す（存在しない場合は空のリスト）
        return filtered_indices


    # テキストを取得
    def retrieve_text(self, index):
        # print('@@@@@ common/chatapi_call_first.py : def retrieve_text  @@@@@')

        filtered_df = self.parquet_df[self.parquet_df['index-no'] == index]
        if not filtered_df.empty:
            data = filtered_df.to_dict('records')[0]
            text = data['文章要約']
            index_no = data['index-no']
            return text, index_no
        else:
            return "", None
