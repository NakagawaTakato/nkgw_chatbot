import openai

class Translator_ja:
    def __init__(self, api_key):
        print('@@@@@ common/translator_ja.py : def __init__  @@@@@')  
        self.api_key = api_key

    def translate_to_japanese(self, text):
        print('@@@@@ common/translator_ja.py : translate_to_japanese  @@@@@')  

        openai.api_key = self.api_key
        # 言語を判定するプロンプト
        detect_prompt = [
            {"role": "system", "content": "You are a language detection assistant."},
            {"role": "user", "content": f"Detect the language of the following text and respond with the language code (e.g., 'en' for English, 'ja' for Japanese):\n\n{text}"}
        ]
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=detect_prompt,
            temperature = 0.0
        )
        language_code = response.choices[0].message.content.strip()

        # 日本語でない場合、翻訳するプロンプト
        print('@@@@@ common/translator_ja.py : language_code  @@@@@', language_code)  
        if language_code != 'ja':
            print('@@@@@ common/translator_ja.py : point03  @@@@@')  
            translate_prompt = [
                {"role": "system", "content": "You are a translation assistant."},
                {"role": "user", "content": f"Translate the following text to Japanese:\n\n{text}"}
            ]
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=translate_prompt,
                temperature = 0.0
            )
            translated_text = response.choices[0].message.content.strip()
            return translated_text

        # 日本語の場合、そのまま返す
        return text