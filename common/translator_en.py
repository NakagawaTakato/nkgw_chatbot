import openai

class Translator_en:
    def __init__(self, api_key):
        print('@@@@@ common/translator_en.py : def __init__  @@@@@')  
        self.api_key = api_key

    def translate_to_english(self, text):

        openai.api_key = self.api_key

        # 英語に翻訳するプロンプト
        translate_prompt = [
            {"role": "system", "content": "You are a translation assistant."},
            {"role": "user", "content": f"Translate the following text to English:\n\n{text}"}
        ]
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=translate_prompt,
            temperature = 0.0
        )
        translated_text = response.choices[0].message.content.strip()
        return translated_text