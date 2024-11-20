from twikit import Client
import json
import os
from datetime import datetime, timezone
import asyncio

class TwitterFollowerSearch:
    """Twitterフォロワーのツイートを検索・保存するクラス"""
    
    def __init__(self):
        # Twitterクライアントの初期化（英語設定）
        self.client = Client(language='en-US')
        # クッキー情報を保存しているJSONファイルのパス
        self.cookie_path = "twitter_json/cookie_edit.json"
        # 検索結果を保存するディレクトリ
        self.results_dir = "search_results"
        # 保存ディレクトリがない場合は作成
        os.makedirs(self.results_dir, exist_ok=True)

    async def setup(self):
        """認証設定を行い、クライアントを初期化"""
        try:
            # クッキーファイルから認証情報を読み込み
            with open(self.cookie_path, 'r', encoding='utf-8') as file:
                cookies = json.load(file)
            self.client.set_cookies(cookies)
            
            # ユーザーIDを取得し認証を確認
            self.user_id = await self.client.user_id()
            user = await self.client.get_user_by_id(self.user_id)
            print(f"認証成功: @{user.screen_name}")
            return True
        except Exception as e:
            print(f"認証エラー: {e}")
            return False

    async def get_followers_tweets(self, count=10):
        """フォロワーの今日のツイートを取得"""
        try:
            tweets = []
            print("フォロワーの今日のツイートを取得中...")
            
            # フォロワーを最大3人に制限（レート制限対策）
            followers = await self.client.get_latest_followers(count=3)
            today = datetime.now(timezone.utc)
            
            for i, follower in enumerate(followers):
                # 15リクエストごとに15秒待機
                if i > 0 and i % 1 == 0:
                    print("APIレート制限を回避するため15秒待機します...")
                    await asyncio.sleep(15)
                
                try:
                    # 各フォロワーの最新ツイートを2件に制限
                    timeline = await self.client.get_user_tweets(
                        follower.id, 
                        tweet_type='Tweets',
                        count=2
                    )
                    
                    for tweet in timeline:
                        tweet_date = datetime.strptime(
                            tweet.created_at, 
                            '%a %b %d %H:%M:%S %z %Y'
                        )
                        
                        if tweet_date.date() == today.date():
                            tweet_data = {
                                'user_name': tweet.user.name,
                                'screen_name': tweet.user.screen_name,
                                'text': tweet.text,
                                'created_at': tweet.created_at,
                                'retweet_count': tweet.retweet_count,
                                'like_count': tweet.favorite_count,
                                'view_count': tweet.view_count,
                                'tweet_id': tweet.id,
                                'lang': tweet.lang,
                                'possibly_sensitive': tweet.possibly_sensitive
                            }
                            tweets.append(tweet_data)
                            
                            if len(tweets) >= count:
                                return tweets
                                
                except Exception as e:
                    print(f"ユーザー @{follower.screen_name} のツイート取得でエラー: {e}")
                    continue

            return tweets
        except Exception as e:
            print(f"ツイート取得エラー: {e}")
            return []

    def save_tweets(self, tweets):
        """取得したツイートをJSONファイルとして保存"""
        try:
            # タイムスタンプを含むファイル名を生成
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(
                self.results_dir, 
                f"followers_tweets_{current_time}.json"
            )
            
            # JSON形式で保存（日本語対応）
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            print(f"ツイートを保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"保存エラー: {e}")
            return None

async def main():
    # TwitterFollowerSearchインスタンスを作成
    searcher = TwitterFollowerSearch()
    
    # 認証設定を実行
    if not await searcher.setup():
        return

    # ツイートを取得（最大10件）
    tweets = await searcher.get_followers_tweets(count=10)

    # 取得結果を表示
    print(f"\n取得結果 ({len(tweets)}件のツイート):")
    for tweet in tweets:
        print("\n-------------------")
        print(f"ユーザー: @{tweet['screen_name']} ({tweet['user_name']})")
        print(f"ツイート: {tweet['text']}")
        print(f"投稿日時: {tweet['created_at']}")
        print(f"統計: {tweet['retweet_count']}RT, {tweet['like_count']}いいね, {tweet['view_count']}表示")
        print(f"言語: {tweet['lang']}")

    # ツイートが存在する場合はファイルに保存
    if tweets:
        searcher.save_tweets(tweets)

if __name__ == "__main__":
    asyncio.run(main())