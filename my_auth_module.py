import os
import base64
import tweepy
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime
import http.client

# ロギングの設定
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# HTTPレスポンスのデバッグレベルを1に設定
#http.client.HTTPConnection.debuglevel = 1

def get_bearer_token(consumer_key, consumer_secret):
#    token_url = "https://api.twitter.com/oauth2/token"
    token_url = "https://api.twitter.com/oauth/request_token"
    
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "tweet.read tweet.write users.read follows.read follows.write offline.access"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code != 200:
        logging.error(f"トークン取得に失敗しました。ステータスコード: {response.status_code}")
        logging.error(f"レスポンス内容: {response.text}")
        return None
    
    token_data = response.json()
    
    if "access_token" not in token_data or token_data.get("token_type") != "bearer":
        logging.error(f"予期しないレスポンス形式: {token_data}")
        return None
    
    logging.info("Bearer トークンの取得に成功しました。")
    return token_data["access_token"]

def get_x_client(bearer_token):
    auth = tweepy.OAuth2BearerHandler(bearer_token)
    return tweepy.API(auth)

def get_user_info(api, username):
    try:
        user = api.get_user(screen_name=username)
        logging.debug(f"User Info: {user._json}")
        return user._json
    except tweepy.errors.NotFound:
        logging.error(f"ユーザー '{username}' が見つかりません。")
    except tweepy.errors.Unauthorized:
        logging.error("認証エラーが発生しました。APIキーとアクセストークンを確認してください。")
    except tweepy.errors.TooManyRequests:
        logging.error("API制限に達しました。しばらく待ってから再試行してください。")
    except Exception as e:
        logging.error(f"ユーザー情報の取得中に予期せぬエラーが発生しました: {e}")
    return None

def get_user_tweets(api, user_id):
    try:
        tweets = api.user_timeline(user_id=user_id, count=5)
        logging.debug(f"Tweets: {[tweet._json for tweet in tweets]}")
        return [tweet._json for tweet in tweets]
    except tweepy.errors.NotFound:
        logging.error(f"ユーザーID '{user_id}' が見つかりません。")
    except tweepy.errors.Unauthorized:
        logging.error("認証エラーが発生しました。APIキーとアクセストークンを確認してください。")
    except tweepy.errors.TooManyRequests:
        logging.error("API制限に達しました。しばらく待ってから再試行してください。")
    except Exception as e:
        logging.error(f"ツイートの取得中に予期せぬエラーが発生しました: {e}")
    return None

def post_tweet(api, text):
    try:
        tweet = api.update_status(text)
        #tweet = api.create_tweet(text)
        logging.info(f"ツイートを投稿しました。Tweet ID: {tweet.id}")
        return tweet._json
    except tweepy.errors.Unauthorized:
        logging.error("認証エラーが発生しました。APIキーとアクセストークンを確認してください。")
    except tweepy.errors.Forbidden:
        logging.error("ツイートの投稿が禁止されています。アプリケーションの権限を確認してください。")
    except tweepy.errors.TooManyRequests:
        logging.error("API制限に達しました。しばらく待ってから再試行してください。")
    except Exception as e:
        logging.error(f"ツイートの投稿中に予期せぬエラーが発生しました: {e}")
    return None

if __name__ == "__main__":
    load_dotenv()
    consumer_key = os.getenv("X_CONSUMER_KEY")
    consumer_secret = os.getenv("X_CONSUMER_SECRET")

    if not all([consumer_key, consumer_secret]):
        logging.error("エラー: X_CONSUMER_KEY または X_CONSUMER_SECRET が設定されていません。")
        exit(1)

    bearer_token = get_bearer_token(consumer_key, consumer_secret)
    if bearer_token:
        api = get_x_client(bearer_token)
        logging.info("X クライアントの認証に成功しました。")
        
        # # @kabuco_hのユーザー情報を取得
        # user = get_user_info(api, "kabuco_h")
        # if user:
        #     logging.info(f"@kabuco_h のフォロワー数: {user['followers_count']}")
        
        # # @kabuco_hの最新ツイートを取得
        # if user:
        #     tweets = get_user_tweets(api, user['id'])
        #     if tweets:
        #         logging.info(f"@kabuco_h の最新ツイート: {tweets[0]['text']}")
        #     else:
        #         logging.info("ツイートが見つかりませんでした。")
                
        # テスト投稿
        test_tweet = "これはテスト投稿です。#TestTweet " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        posted_tweet = post_tweet(api, test_tweet)
        if posted_tweet:
            logging.info(f"テスト投稿成功: {posted_tweet['text']}")
        else:
            logging.error("テスト投稿に失敗しました。")
            
    else:
        logging.error("Bearer tokenの取得に失敗しました。")