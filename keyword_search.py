from twikit import Client
import json
import os
from datetime import datetime
import asyncio

class TwitterKeywordAnalyzer:
    def __init__(self):
        # Twitterクライアントを英語（米国）設定で初期化
        self.client = Client(language='en-US')
        # 認証クッキーのパス
        self.cookie_path = "twitter_json/cookie_edit.json"
        # 結果を保存するディレクトリ
        self.results_dir = "keyword_search_results"
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

    async def search_with_keyword(self, keyword, count=20, sort_by='latest'):
        """キーワードを含むツイートを検索し、関連情報を取得する"""
        try:
            search_results = []
            print(f"'{keyword}' に関連する情報を検索中...(並び順: {sort_by})")

            # 検索タイプの設定（新しい順か人気順）
            product_type = 'Latest' if sort_by == 'latest' else 'Top'
            
            # ツイート検索
            results = await self.client.search_tweet(
                query=keyword,
                product=product_type,
                count=min(count, 20)
            )

            for tweet in results:
                # ツイート投稿者の詳細情報を取得
                user_data = {
                    'user_id': tweet.user.id,
                    'name': tweet.user.name,
                    'screen_name': tweet.user.screen_name,
                    'profile_description': tweet.user.description,
                    'profile_url': f"https://twitter.com/{tweet.user.screen_name}",
                    'followers_count': tweet.user.followers_count,
                    'following_count': tweet.user.following_count,
                    'profile_image_url': tweet.user.profile_image_url,
                    'location': tweet.user.location
                }

                # ツイートの情報を取得
                tweet_data = {
                    'tweet_id': tweet.id,
                    'tweet_url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.retweet_count,
                    'like_count': tweet.favorite_count,
                    'reply_count': tweet.reply_count if hasattr(tweet, 'reply_count') else 0,
                    'is_retweet': bool(tweet.retweeted_tweet),
                    'is_quote': tweet.is_quote_status,
                    'language': tweet.lang
                }

                # キーワードの出現場所を確認
                keyword_locations = []
                if keyword.lower() in tweet.text.lower():
                    keyword_locations.append('tweet_text')
                if keyword.lower() in tweet.user.description.lower():
                    keyword_locations.append('profile_description')
                if keyword.lower() in tweet.user.name.lower():
                    keyword_locations.append('user_name')
                if keyword.lower() in tweet.user.screen_name.lower():
                    keyword_locations.append('screen_name')

                search_results.append({
                    'user': user_data,
                    'tweet': tweet_data,
                    'keyword_locations': keyword_locations
                })

            # いいね数順でソートする場合
            if sort_by == 'likes':
                search_results.sort(key=lambda x: x['tweet']['like_count'], reverse=True)

            return search_results

        except Exception as e:
            print(f"検索エラー: {e}")
            return []

    def save_results(self, results, filename_prefix):
        """検索結果をJSONファイルとして保存する"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_dir}/{filename_prefix}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(results, file, ensure_ascii=False, indent=2, default=str)
            print(f"\n結果を保存しました: {filename}")
        except Exception as e:
            print(f"結果の保存中にエラーが発生しました: {e}")

async def main():
    analyzer = TwitterKeywordAnalyzer()
    
    if not await analyzer.setup():
        return

    # 検索設定
    keyword = "プログラミング"  # 検索したいキーワード
    count = 10  # 取得する結果の数
    
    # 検索オプション選択
    print("\n検索オプション:")
    print("1: 新しい順")
    print("2: 人気順")
    print("3: いいね数順")
    
    try:
        option = int(input("検索オプションを選択してください (1-3): "))
        sort_by = {
            1: 'latest',
            2: 'top',
            3: 'likes'
        }.get(option, 'latest')
    except ValueError:
        print("無効な入力です。デフォルトの'新しい順'で検索します。")
        sort_by = 'latest'

    # キーワード検索を実行
    results = await analyzer.search_with_keyword(keyword, count, sort_by)

    if not results:
        print("検索結果が見つかりませんでした。")
        return

    # 検索結果を表示
    sort_type = {
        'latest': '新しい順',
        'top': '人気順',
        'likes': 'いいね数順'
    }[sort_by]
    
    print(f"\n検索結果 ({len(results)} 件) - {sort_type}:")
    for result in results:
        print("\n" + "="*50)
        user = result['user']
        tweet = result['tweet']
        locations = result['keyword_locations']

        # 投稿日時といいね数を先に表示
        print(f"投稿日時: {tweet['created_at']}")
        print(f"いいね数: {tweet['like_count']}")

        print(f"\nユーザー情報:")
        print(f"名前: {user['name']} (@{user['screen_name']})")
        print(f"プロフィール: {user['profile_description']}")
        print(f"アカウントURL: {user['profile_url']}")
        print(f"フォロワー: {user['followers_count']}, フォロー中: {user['following_count']}")
        
        print(f"\nツイート情報:")
        print(f"テキスト: {tweet['text']}")
        print(f"ツイートURL: {tweet['tweet_url']}")
        print(f"リツイート: {tweet['retweet_count']}")
        
        print(f"\nキーワード '{keyword}' の出現場所: {', '.join(locations)}")

    # 結果を保存（ファイル名にソート方法を含める）
    if results:
        analyzer.save_results(results, f"{keyword}_{sort_by}")

if __name__ == "__main__":
    asyncio.run(main())