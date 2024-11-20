"""
Twitter半自動投稿パイプライン
目的: ツイートの収集、AI投稿文生成、手動確認を経た投稿の自動化
機能:
- Twitter APIによるツイート収集
- Google Sheetsへのデータ保存
- OpenAI APIによる投稿文生成
- 手動確認プロセス
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict
import json
import openai
from twikit.client import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class TwitterAutomationPipeline:
    def __init__(self, twitter_cookies_path: str, openai_key: str, sheets_creds_path: str):
        """
        パイプラインの初期化
        Args:
            twitter_cookies_path: Twitterクッキーファイルのパス
            openai_key: OpenAI APIキー
            sheets_creds_path: Google Sheets認証情報のパス
        """
        # Twitter APIクライアントを日本語で初期化
        self.twitter_client = Client(language='ja-JP')
        self.cookies_path = twitter_cookies_path
        self.openai_key = openai_key
        self.sheets_creds_path = sheets_creds_path
        
    async def setup(self):
        """各APIクライアントの初期化とセットアップ"""
        # Twitterクッキーの読み込みと設定
        with open(self.cookies_path, 'r') as f:
            cookies = json.load(f)
        self.twitter_client.set_cookies(cookies)
        
        # OpenAI APIキーの設定
        openai.api_key = self.openai_key
        
        # Google Sheets APIクライアントのセットアップ
        self.sheets_service = self._setup_sheets_service()
        
    def _setup_sheets_service(self):
        """
        Google Sheets APIクライアントのセットアップ
        Returns:
            設定済みのGoogle Sheets APIサービスオブジェクト
        """
        creds = Credentials.from_authorized_user_file(
            self.sheets_creds_path, 
            ['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds)
        
    async def collect_tweets(self, search_query: str, count: int = 20) -> List[Dict]:
        """
        ステップ1: Twitter APIを使用してツイートを収集
        Args:
            search_query: 検索キーワード
            count: 取得するツイート数
        Returns:
            収集したツイート情報のリスト
        """
        tweets = []
        # Twitter APIで検索実行
        results = await self.twitter_client.search_tweet(
            query=search_query, 
            product='Top',  # 人気順で取得
            count=count
        )
        
        # 各ツイートのデータを抽出
        for tweet in results:
            tweet_data = {
                'text': tweet.text,  # ツイート本文
                'reply_count': tweet.reply_count,  # リプライ数
                'url': f'https://twitter.com/i/web/status/{tweet.id}',  # ツイートURL
                # エンゲージメントスコアの計算（リプライ数+いいね数+リツイート数）
                'engagement_score': tweet.reply_count + tweet.favorite_count + tweet.retweet_count,
                'created_at': tweet.created_at  # 投稿日時
            }
            tweets.append(tweet_data)
            
        return tweets
    
    def save_to_sheets(self, spreadsheet_id: str, tweets: List[Dict]):
        """
        収集したツイートをGoogle Sheetsに保存
        Args:
            spreadsheet_id: 保存先のスプレッドシートID
            tweets: 保存するツイートデータのリスト
        """
        # スプレッドシートに書き込むデータの整形
        values = [[
            tweet['created_at'],     # A列: 投稿日時
            tweet['text'],           # B列: ツイート本文
            tweet['reply_count'],    # C列: リプライ数
            tweet['url'],            # D列: URL
            tweet['engagement_score'] # E列: エンゲージメントスコア
        ] for tweet in tweets]
        
        # Google Sheetsへの書き込み実行
        body = {'values': values}
        self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:E',  # A列からE列に書き込み
            valueInputOption='RAW',
            body=body
        ).execute()
        
    async def generate_post(self, tweet_data: Dict) -> str:
        """
        ステップ2: AIを使用して投稿文を生成
        Args:
            tweet_data: 参考にするツイートデータ
        Returns:
            生成された投稿文
        """
        # AIへの指示プロンプト
        prompt = f"""
以下のツイートを参考に、新しい投稿文を作成してください。
オリジナルツイート: {tweet_data['text']}
要件:
- オリジナルの内容を尊重しつつ、独自の視点を加える
- 簡潔で読みやすい文章にする
- ハッシュタグを1-2個付ける
- 全体で140文字以内に収める
"""
        
        # OpenAI APIを使用して投稿文を生成
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
        
    async def post_tweet(self, content: str, image_path: str = None) -> bool:
        """
        ステップ3: 手動確認後にツイートを投稿
        Args:
            content: 投稿する文章
            image_path: 添付画像のパス（オプション）
        Returns:
            投稿成功時True、キャンセルまたは失敗時False
        """
        # 投稿内容の確認表示
        print("\n=== 投稿前確認 ===")
        print(f"投稿内容: {content}")
        if image_path:
            print(f"添付画像: {image_path}")
            
        # 手動承認の要求
        confirm = input("\n投稿を承認しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("投稿がキャンセルされました")
            return False
            
        try:
            # 画像がある場合はアップロード
            media_id = None
            if image_path:
                media_id = await self.twitter_client.upload_media(image_path)
                
            # ツイートの投稿
            await self.twitter_client.create_tweet(
                text=content,
                media_ids=[media_id] if media_id else None
            )
            print("投稿が完了しました")
            return True
        except Exception as e:
            print(f"投稿エラー: {e}")
            return False

async def main():
    """メイン実行関数"""
    # パイプラインの初期化
    pipeline = TwitterAutomationPipeline(
        twitter_cookies_path="cookies.json",
        openai_key="your-openai-key",
        sheets_creds_path="sheets_credentials.json"
    )
    await pipeline.setup()
    
    # ステップ1: ツイートの収集と保存
    tweets = await pipeline.collect_tweets("Python programming")
    pipeline.save_to_sheets("your-spreadsheet-id", tweets)
    
    # エンゲージメントの高い順にソート
    sorted_tweets = sorted(tweets, key=lambda x: x['engagement_score'], reverse=True)
    
    # 上位3つのツイートを処理
    for tweet in sorted_tweets[:3]:
        # ステップ2: AI投稿文の生成
        generated_content = await pipeline.generate_post(tweet)
        
        # ステップ3: 手動確認と投稿
        await pipeline.post_tweet(generated_content)
        
        # 投稿間隔を設定（5分）
        await asyncio.sleep(300)

if __name__ == "__main__":
    # スクリプトの実行
    asyncio.run(main())