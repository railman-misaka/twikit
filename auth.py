import json
import sys
import os
from twikit import Client
import asyncio

class TwitterCookieHandler:
    def __init__(self, input_path="twitter_json/cookie.json", output_path="twitter_json/cookie_edit.json"):
        self.input_path = input_path
        self.output_path = output_path

    def convert_json(self):
        """Cookie-Editorから出力されたJSONを変換する"""
        try:
            # 入力JSONの読み込み
            with open(self.input_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"エラー: {self.input_path} が見つかりません。")
            return False
        except json.JSONDecodeError:
            print("エラー: JSONの形式が正しくありません。")
            return False

        # Cookie形式の変換
        result = {}
        for item in data:
            name = item.get("name")
            value = item.get("value")
            if name and value:
                result[name] = value

        # 変換後のJSONを保存
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            with open(self.output_path, 'w', encoding='utf-8') as file:
                json.dump(result, file, sort_keys=True, indent=4)
            return True
        except Exception as e:
            print(f"エラー: 変換後のJSONの保存に失敗しました: {e}")
            return False

class TwitterClient:
    def __init__(self):
        self.client = Client('en-US')
        self.cookie_path = "twitter_json/cookie_edit.json"

    async def initialize(self):
        """クライアントの初期化とCookieのロード"""
        if not os.path.isfile(self.cookie_path):
            print(f"エラー: {self.cookie_path} が見つかりません。")
            return False
        
        try:
            # Cookieファイルを読み込む
            with open(self.cookie_path, 'r', encoding='utf-8') as file:
                cookies = json.load(file)
            # クライアントにCookieを設定
            self.client.cookies = cookies
            return True
        except Exception as e:
            print(f"エラー: Cookieのロードに失敗しました: {e}")
            return False

async def main():
    # Cookie変換処理
    cookie_handler = TwitterCookieHandler()
    if not cookie_handler.convert_json():
        return

    # クライアント初期化
    client = TwitterClient()
    if not await client.initialize():
        return

    print("認証が完了しました。")
    return client

if __name__ == "__main__":
    asyncio.run(main())