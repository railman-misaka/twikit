from twikit import Client
import json
import os
from datetime import datetime
import asyncio

class TwitterKeywordSearch:
    def __init__(self):
        # Twitterクライアントを英語（米国）設定で初期化
        self.client = Client(language='en-US')
        # 認証クッキーのパス
        self.cookie_path = "twitter_json/cookie_edit.json"
        # ツイート検索結果を保存するディレクトリ
        self.results_dir = "search_results"
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
            # 認証中にエラーが発生した場合のエラーメッセージを表示
            print(f"認証エラー: {e}")
            return False

    async def search_tweets(self, keyword, count=10):
        """指定したキーワードでツイートを検索する"""
        try:
            tweets = []
            print(f"'{keyword}' を検索中...")
            # Twitter APIを使用してツイートを検索
            results = await self.client.search_tweet(
                query=keyword,
                product='Top',
                count=min(count, 20)  # 一度のリクエストで取得できるツイート数は20が上限
            )
            
            for tweet in results:
                # 各ツイートのデータを辞書形式で整理
                tweet_data = {
                    'user_name': tweet.user.name,                    # ユーザーの名前
                    'screen_name': tweet.user.screen_name,          # ユーザーのスクリーンネーム
                    'text': tweet.text,                              # ツイートのテキスト内容
                    'created_at': tweet.created_at,                  # ツイートの作成日時
                    'retweet_count': tweet.retweet_count,            # リツイート数
                    'like_count': tweet.favorite_count,              # いいね数
                    'tweet_id': tweet.id                             # ツイートのID
                }
                tweets.append(tweet_data)
                
                # 指定された数のツイートを取得したらループを終了
                if len(tweets) >= count:
                    break
                    
            # さらにツイートが必要な場合、次のカーソルを使用して追加取得
            if len(tweets) < count and results.next_cursor:
                more_results = await results.next()
                for tweet in more_results:
                    if len(tweets) >= count:
                        break
                    tweet_data = {
                        'user_name': tweet.user.name,
                        'screen_name': tweet.user.screen_name,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'retweet_count': tweet.retweet_count,
                        'like_count': tweet.favorite_count,
                        'tweet_id': tweet.id
                    }
                    tweets.append(tweet_data)
            
            return tweets
        except Exception as e:
            # 検索中にエラーが発生した場合のエラーメッセージを表示
            print(f"検索エラー: {e}")
            return []

    def save_tweets(self, tweets, keyword):
        """検索結果のツイートをJSONファイルとして保存する"""
        try:
            # 現在の日時を取得してファイル名に含める
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            # キーワードから安全なファイル名を生成（英数字、スペース、ハイフン、アンダースコアのみ）
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = os.path.join(
                self.results_dir, 
                f"search_{safe_keyword}_{current_time}.json"
            )
            
            # ツイートデータをJSON形式でファイルに保存
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            print(f"ツイートを保存しました: {filename}")
            return filename
        except Exception as e:
            # 保存中にエラーが発生した場合のエラーメッセージを表示
            print(f"保存エラー: {e}")
            return None

async def main():
    # TwitterKeywordSearchクラスのインスタンスを作成
    searcher = TwitterKeywordSearch()
    
    # 認証設定を実行し、失敗した場合は処理を終了
    if not await searcher.setup():
        return

    # 検索キーワードと取得するツイートの数を設定
    keyword = "@railman_misaka"
    count = 10

    # 指定したキーワードで
    # ツイートを検索
    tweets = await searcher.search_tweets(keyword, count)

    # 検索結果を表示
    print(f"\n検索結果 ({len(tweets)} 件):")
    for tweet in tweets:
        print("\n-------------------")
        print(f"ユーザー: @{tweet['screen_name']} ({tweet['user_name']})")
        print(f"ツイート: {tweet['text']}")
        print(f"投稿日時: {tweet['created_at']}")
        print(f"リツイート数: {tweet['retweet_count']}, いいね数: {tweet['like_count']}")

    # ツイートが存在する場合、JSONファイルとして保存
    if tweets:
        searcher.save_tweets(tweets, keyword)

if __name__ == "__main__":
    # メイン関数を非同期で実行
    asyncio.run(main())