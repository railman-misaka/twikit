from twikit import Client
import json
import os
from datetime import datetime
import asyncio
from collections import Counter

class TwitterProfileAnalyzer:
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

    async def analyze_user_replies(self, screen_name, tweets_to_analyze=200):
        """指定したユーザーのツイートから、リプライを分析する"""
        try:
            # ユーザー情報を取得
            target_user = await self.client.get_user_by_screen_name(screen_name)
            print(f"{screen_name}のツイートを分析中...")

            # リプライしているユーザーをスクリーンネームベースで追跡
            reply_counter = Counter()
            reply_users = {}
            
            # ツイートを取得（リプライを含む）
            print("ツイートを取得中...")
            results = await self.client.get_user_tweets(
                target_user.id,
                tweet_type='Replies',  # Repliesタイプに変更
                count=min(tweets_to_analyze, 100)
            )

            analyzed_count = 0
            while results and analyzed_count < tweets_to_analyze:
                for tweet in results:
                    try:
                        # リプライ先のツイートテキストを解析
                        if hasattr(tweet, 'text') and tweet.text.startswith('@'):
                            # @ユーザー名を抽出
                            mentioned_users = [
                                word[1:] for word in tweet.text.split()
                                if word.startswith('@')
                            ]
                            
                            for reply_to in mentioned_users:
                                if reply_to and reply_to != screen_name:
                                    try:
                                        if reply_to not in reply_users:
                                            # スクリーンネームからユーザー情報を取得
                                            try:
                                                reply_user = await self.client.get_user_by_screen_name(reply_to)
                                                reply_users[reply_to] = reply_user
                                                print(f"ユーザー {reply_to} の情報を取得しました")
                                            except Exception as e:
                                                continue
                                        reply_counter[reply_to] += 1
                                    except Exception as e:
                                        print(f"ユーザー {reply_to} の情報取得をスキップ: {e}")
                                        continue
                    except Exception as e:
                        continue
                    
                    analyzed_count += 1
                    if analyzed_count % 20 == 0:
                        print(f"{analyzed_count}件のツイートを分析済み")
                    
                if analyzed_count < tweets_to_analyze and results.next_cursor:
                    try:
                        results = await results.next()
                    except Exception as e:
                        print(f"追加ツイート取得エラー: {e}")
                        break
                else:
                    break

            print(f"\n分析完了: {analyzed_count}件のツイートを処理")
            print(f"リプライ先ユーザー数: {len(reply_users)}人")
            
            return reply_counter, reply_users

        except Exception as e:
            print(f"分析エラー: {e}")
            return Counter(), {}

    async def get_user_profile(self, user):
        """ユーザーのプロフィール情報を取得する"""
        try:
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
            return profile_data
        except Exception as e:
            print(f"プロフィール取得エラー: {e}")
            return None

    async def get_user_tweets(self, user, count=1):
        """ユーザーの投稿を取得する"""
        try:
            tweets = []
            results = await user.get_tweets(tweet_type='Tweets', count=count)
            
            for tweet in results:
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

    def save_results(self, frequent_repliers_data, target_screen_name):
        """分析結果をJSONファイルとして保存する"""
        try:
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(
                self.results_dir, 
                f"analysis_{target_screen_name}_{current_time}.json"
            )
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(frequent_repliers_data, f, ensure_ascii=False, indent=2)
            print(f"分析結果を保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"保存エラー: {e}")
            return None

async def main():
    analyzer = TwitterProfileAnalyzer()
    
    if not await analyzer.setup():
        return

    # 分析対象のユーザー名を指定（@を除いた名前）
    target_user = "shibuyu_tech"
    min_replies = 3  # 最小リプライ数の閾値
    tweets_to_analyze = 200  # 分析するツイート数

    print(f"\n{target_user}のリプライを分析します...")
    print(f"- 分析対象ツイート数: {tweets_to_analyze}")
    print(f"- 最小リプライ数: {min_replies}")

    # リプライを分析
    reply_counter, reply_users = await analyzer.analyze_user_replies(target_user, tweets_to_analyze)
    
    if not reply_counter:
        print("\nリプライが見つかりませんでした。")
        return

    # 頻繁にリプライしているユーザーの情報を収集
    frequent_repliers_data = []
    print("\nリプライの多いユーザーの情報を収集中...")
    
    for screen_name, reply_count in reply_counter.most_common():
        if reply_count >= min_replies and screen_name in reply_users:
            try:
                user = reply_users[screen_name]
                profile_data = await analyzer.get_user_profile(user)
                tweets = await analyzer.get_user_tweets(user, count=3)
                
                if profile_data:
                    user_data = {
                        'profile': profile_data,
                        'reply_count': reply_count,
                        'recent_tweets': tweets
                    }
                    frequent_repliers_data.append(user_data)
                    print(f"@{screen_name}の情報を取得しました（リプライ数: {reply_count}）")
            except Exception as e:
                print(f"@{screen_name}の情報取得に失敗: {e}")
                continue
    
    # 結果を表示
    if not frequent_repliers_data:
        print(f"\n{min_replies}回以上リプライしているユーザーは見つかりませんでした。")
        return

    print(f"\n{min_replies}回以上リプライしているユーザー ({len(frequent_repliers_data)}人):")
    for user_data in frequent_repliers_data:
        profile = user_data['profile']
        print("\n-------------------")
        print(f"名前: {profile['name']} (@{profile['screen_name']})")
        print(f"プロフィール: {profile['description']}")
        print(f"リプライ数: {user_data['reply_count']}")
        print(f"フォロワー: {profile['followers_count']}, フォロー中: {profile['following_count']}")
        
        if user_data['recent_tweets']:
            print("\n最近のツイート:")
            for tweet in user_data['recent_tweets']:
                print(f"- {tweet['text']}")

    # 結果を保存
    if frequent_repliers_data:
        analyzer.save_results(frequent_repliers_data, target_user)

if __name__ == "__main__":
    asyncio.run(main())