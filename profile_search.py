from twikit import Client
import json
import os
from datetime import datetime
import asyncio

class TwitterProfileFetcher:
    def __init__(self):
        # Twitterクライアントを英語（米国）設定で初期化
        self.client = Client(language='en-US')
        # 認証クッキーのパス
        self.cookie_path = "twitter_json/cookie_edit.json"
        # 結果を保存するディレクトリ
        self.results_dir = "profile_results"
        # 結果保存用ディレクトリが存在しない場合は作成
        os.makedirs(self.results_dir, exist_ok=True)

    async def setup(self):
        """クッキーを使用して認証を設定する"""
        try:
            # クッキーファイルを開き、JSONデータを読み込む
            with open(self.cookie_path, 'r', encoding='utf-8') as file:
                cookies = json.load(file)
            # クライアントにクッキーを設定
            self.client.set_cookies(cookies)
            print("認証に成功しました！")
            return True
        except Exception as e:
            print(f"認証エラー: {e}")
            return False

    async def get_user_profile(self, screen_name):
        """ユーザーのプロフィール情報を取得する"""
        try:
            # スクリーンネームからユーザー情報を取得
            user = await self.client.get_user_by_screen_name(screen_name)
            
            # プロフィール情報を辞書形式で整理
            profile_data = {
                'user_id': user.id,                      # ユーザーID
                'name': user.name,                       # 表示名
                'screen_name': user.screen_name,         # @ユーザー名
                'description': user.description,         # プロフィール文
                'location': user.location,               # 場所
                'followers_count': user.followers_count, # フォロワー数
                'following_count': user.following_count, # フォロー数
                'tweets_count': user.statuses_count,    # ツイート数
                'created_at': user.created_at,          # アカウント作成日
                'profile_image_url': user.profile_image_url  # プロフィール画像URL
            }
            return profile_data, user
        except Exception as e:
            print(f"プロフィール取得エラー: {e}")
            return None, None

    async def get_user_tweets(self, user, count=1):
        """ユーザーの投稿を取得する"""
        try:
            tweets = []
            # ユーザーの投稿を取得
            results = await user.get_tweets(tweet_type='Tweets', count=count)
            
            for tweet in results:
                # 各ツイートのデータを辞書形式で整理
                tweet_data = {
                    'tweet_id': tweet.id,                # ツイートID
                    'text': tweet.text,                  # ツイート本文
                    'created_at': tweet.created_at,      # 投稿日時
                    'retweet_count': tweet.retweet_count, # リツイート数
                    'like_count': tweet.favorite_count,   # いいね数
                    'reply_count': tweet.reply_count,     # 返信数
                    'is_retweet': bool(tweet.retweeted_tweet), # リツイートかどうか
                    'is_quote': tweet.is_quote_status     # 引用ツイートかどうか
                }
                tweets.append(tweet_data)
            
            return tweets
        except Exception as e:
            print(f"ツイート取得エラー: {e}")
            return []

    def save_results(self, profile_data, tweets, screen_name):
        """プロフィールと投稿をJSONファイルとして保存する"""
        try:
            # 現在の日時を取得してファイル名に含める
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(
                self.results_dir, 
                f"profile_{screen_name}_{current_time}.json"
            )
            
            # プロフィールとツイートのデータを結合
            save_data = {
                'profile': profile_data,
                'tweets': tweets
            }
            
            # データをJSON形式でファイルに保存
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"データを保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"保存エラー: {e}")
            return None

async def main():
    # TwitterProfileFetcherクラスのインスタンスを作成
    fetcher = TwitterProfileFetcher()
    
    # 認証設定を実行
    if not await fetcher.setup():
        return

    # 取得したいユーザーのスクリーンネームを指定（@を除いた名前）
    target_user = "railman_misaka"
    tweet_count = 1  # 取得するツイート数

    # プロフィール情報を取得
    profile_data, user = await fetcher.get_user_profile(target_user)
    
    if profile_data and user:
        print("\nプロフィール情報:")
        print(f"名前: {profile_data['name']} (@{profile_data['screen_name']})")
        print(f"プロフィール: {profile_data['description']}")
        print(f"フォロワー: {profile_data['followers_count']}")
        print(f"フォロー中: {profile_data['following_count']}")
        
        # ユーザーの投稿を取得
        tweets = await fetcher.get_user_tweets(user, tweet_count)
        
        print(f"\n最近の投稿 ({len(tweets)} 件):")
        for tweet in tweets:
            print("\n-------------------")
            print(f"投稿: {tweet['text']}")
            print(f"日時: {tweet['created_at']}")
            print(f"リツイート: {tweet['retweet_count']}, いいね: {tweet['like_count']}")
        
        # データを保存
        fetcher.save_results(profile_data, tweets, target_user)

if __name__ == "__main__":
    # メイン関数を非同期で実行
    asyncio.run(main())