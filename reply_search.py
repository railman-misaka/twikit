from twikit import Client
import json
import os
from datetime import datetime
import asyncio
from collections import Counter

class TwitterReplyAnalyzer:
    def __init__(self):
        # Twitterクライアントを英語（米国）設定で初期化
        self.client = Client(language='en-US')
        # 認証クッキーのパス
        self.cookie_path = "twitter_json/cookie_edit.json"
        # 結果を保存するディレクトリ
        self.results_dir = "reply_analysis_results"
        # 結果保存用ディレクトリが存在しない場合は作成
        os.makedirs(self.results_dir, exist_ok=True)

    async def setup(self):
        """クッキーを使用して認証を設定する"""
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as file:
                cookies = json.load(file)
            self.client.set_cookies(cookies)
            print("認証に成功しました！")
            return True
        except Exception as e:
            print(f"認証エラー: {e}")
            return False

    async def get_user_tweets_with_replies(self, screen_name, tweets_to_analyze=200):
        """指定したユーザーのツイートを取得し、リプライを分析する"""
        try:
            # ユーザー情報を取得
            target_user = await self.client.get_user_by_screen_name(screen_name)
            print(f"{screen_name}のツイートを分析中...")

            # リプライしているユーザーをカウント
            reply_counter = Counter()
            
            # ツイートを取得（リプライを含む）
            results = await self.client.get_user_tweets(
                target_user.id,
                tweet_type='Tweets',
                count=min(tweets_to_analyze, 100)  # 一度に取得できる最大数
            )

            analyzed_count = 0
            while results and analyzed_count < tweets_to_analyze:
                for tweet in results:
                    if tweet.in_reply_to and tweet.in_reply_to != target_user.id:
                        reply_counter[tweet.in_reply_to] += 1
                    analyzed_count += 1
                    
                if analyzed_count < tweets_to_analyze and results.next_cursor:
                    results = await results.next()
                else:
                    break

            return reply_counter

        except Exception as e:
            print(f"ツイート取得エラー: {e}")
            return Counter()

    async def get_frequent_repliers_info(self, reply_counter, min_replies=3):
        """頻繁にリプライしているユーザーの詳細情報を取得"""
        frequent_repliers = []
        
        for user_id, reply_count in reply_counter.most_common():
            if reply_count >= min_replies:
                try:
                    # ユーザー情報を取得
                    user = await self.client.get_user_by_id(user_id)
                    
                    # ユーザーの最近のツイートを取得
                    tweets = []
                    results = await user.get_tweets(tweet_type='Tweets', count=10)
                    for tweet in results:
                        tweets.append({
                            'tweet_id': tweet.id,
                            'text': tweet.text,
                            'created_at': tweet.created_at
                        })

                    # ユーザー情報を整理
                    user_data = {
                        'user_id': user.id,
                        'name': user.name,
                        'screen_name': user.screen_name,
                        'description': user.description,
                        'reply_count': reply_count,
                        'followers_count': user.followers_count,
                        'following_count': user.following_count,
                        'tweets': tweets
                    }
                    frequent_repliers.append(user_data)
                    
                except Exception as e:
                    print(f"ユーザー情報取得エラー: {e}")
                    continue

        return frequent_repliers

    def save_results(self, frequent_repliers, target_screen_name):
        """分析結果をJSONファイルとして保存"""
        try:
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(
                self.results_dir, 
                f"reply_analysis_{target_screen_name}_{current_time}.json"
            )
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(frequent_repliers, f, ensure_ascii=False, indent=2)
            print(f"分析結果を保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"保存エラー: {e}")
            return None

async def main():
    analyzer = TwitterReplyAnalyzer()
    
    if not await analyzer.setup():
        return

    # 分析対象のユーザー名を指定（@を除いた名前）
    target_user = "tatsuhara1029"
    min_replies = 3  # 最小リプライ数の閾値

    # リプライを分析
    reply_counter = await analyzer.get_user_tweets_with_replies(target_user)
    
    # 頻繁にリプライしているユーザーの情報を取得
    frequent_repliers = await analyzer.get_frequent_repliers_info(reply_counter, min_replies)
    
    # 結果を表示
    print(f"\n{min_replies}回以上リプライしているユーザー ({len(frequent_repliers)}人):")
    for user in frequent_repliers:
        print("\n-------------------")
        print(f"名前: {user['name']} (@{user['screen_name']})")
        print(f"プロフィール: {user['description']}")
        print(f"リプライ数: {user['reply_count']}")
        print(f"フォロワー: {user['followers_count']}, フォロー中: {user['following_count']}")
        print("\n最近のツイート:")
        for tweet in user['tweets'][:3]:  # 最新3件のみ表示
            print(f"- {tweet['text']}")

    # 結果を保存
    if frequent_repliers:
        analyzer.save_results(frequent_repliers, target_user)

if __name__ == "__main__":
    asyncio.run(main())