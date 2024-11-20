import asyncio
from twikit import Client
import os

async def main():
    try:
        # Clientインスタンスを作成（日本語対応）
        client = Client(language='ja')
        
        # メールアドレスまたは電話番号を auth_info_1 として使用
        # auth_info_2 にユーザー名を指定
        login_result = await client.login(
            auth_info_1='nosnos1014@email.com',  # あなたのメールアドレスに置き換えてください
            auth_info_2='nosnos1014',         # ユーザー名
            password='super1366'              # パスワード
        )
        
        print("ログインに成功しました")
        print(f"ログイン結果: {login_result}")
        
        # ログイン成功後、クッキーを保存（次回のログインで使用可能）
        client.save_cookies('twitter_cookies.json')
        
    except Exception as e:
        print(f"ログイン中にエラーが発生しました: {e}")
        
        # エラーの詳細情報を表示
        if hasattr(e, 'response'):
            print(f"レスポンスステータス: {e.response.status_code}")
            print(f"レスポンス内容: {await e.response.text()}")

if __name__ == "__main__":
    asyncio.run(main())