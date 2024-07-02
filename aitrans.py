import os
import sys
import argparse
import time
import tweepy
from dotenv import load_dotenv
from openai import OpenAI
from openai import RateLimitError, APIError
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import socket
from my_auth_module import get_x_client
import feedparser
import requests
import os
from datetime import datetime, timezone, timedelta

# スクリプトのディレクトリ（または_internal)から.envファイルを読み込む
application_path = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(application_path, ".env")
print(f"{env_path} ファイルから環境変数を読み込みます。")
load_dotenv(env_path)

# load_dotenv()

# .envファイルからAPIキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")



if not openai_api_key:
    print("エラー: OPENAI_API_KEY 環境変数が設定されていません。")
    sys.exit(1)
if not anthropic_api_key:
    print("エラー: ANTHROPIC_API_KEY 環境変数が設定されて��せん。")
    sys.exit(1)

# OpenAI クライアントの初期化
openai_client = OpenAI(api_key=openai_api_key)
# Anthropic クライアントの初期化
anthropic_client = Anthropic(api_key=anthropic_api_key)

def fetch_latest_audio_from_rss(rss_url):
    # RSSフィードを解析
    if not rss_url:
        rss_url = os.getenv("DEFAULT_RSS_URL")
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("フィードにエントリーがありません")
        return None

    # 最新のエントリーを取得
    latest_entry = feed.entries[0]

    # 音声ファイルのURLを探す
    audio_url = None
    for link in latest_entry.links:
        if link.type.startswith('audio/'):
            audio_url = link.href
            break

    if not audio_url:
        print("音声ファイルが見つかりません。")
        return None
    
    audio_page_url = None
    if hasattr( latest_entry, 'link'):
        audio_page_url = latest_entry.link
        print(f"音声ページのURL: {audio_page_url}")

    # ファイル名を生成（日付_タイトル.mp3）
    if hasattr(latest_entry, 'published'):
        published_str = latest_entry.published
        datetime_obj = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S GMT")
        datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)
        jst_timezone = timezone(timedelta(hours=9))
        datetime_obj = datetime_obj.astimezone(jst_timezone)
        date_str = datetime_obj.strftime("%Y%m%d")
    else:
        date_str = datetime.now().strftime("%Y%m%d")

    # date_str = datetime.now().strftime("%Y%m%d")

    title = latest_entry.title
    # ファイル名に使用できない文字を除去
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{date_str}_{safe_title}.m4a"

    # 音声ファイルをダウンロード
    if os.path.exists(filename):
        print(f"ファイル {filename} は既に存在します。ダウンロードせずに終了します。")
        return None, audio_page_url

    print(f"最新エピソード「{title}」をダウンロードしています...")
    response = requests.get(audio_url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"ダウンロード: {filename}")
        return filename, audio_page_url
    else:
        print("ダウンロードに失敗しました。")
        return None, audio_page_url


def transcribe_audio(audio_file_path, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcript.text
        except RateLimitError as e:
            if attempt < max_retries - 1:
                print(f"API制限に達しました。{retry_delay}秒後に再試行します...")
                time.sleep(retry_delay)
            else:
                print("エラー: API制限に達し、最大再試行回数を超えました。")
                print("OpenAIダッシュボードで使用状況を確認し、必要に応じてプランをアップグレードしてください。")
                print("https://platform.openai.com/usage")
                raise
        except APIError as e:
            print(f"APIエラーが発生しました: {e}")
            raise

def read_prompt(file_name):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, file_name)
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except IOError as e:
        print(f"プロンプトファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

def summarize_text(text, title, max_retries=1, retry_delay=5):
    prompt = os.getenv("PROMPT_SUMMARIZE")
    if not prompt:
        print("エラー: PROMPT_SUMMARIZE 環境変数が設定されていません。")
        sys.exit(1)
        
#    print(f"prompt: {prompt}")
    
    for attempt in range(max_retries):
        try:
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\nタイトル：{title}を参考にしてください。\n\nテキスト：{text}"
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"要約中にエラーが発生しました。{retry_delay}秒後に再試行します...")
                time.sleep(retry_delay)
            else:
                print(f"要約に失敗しました: {e}")
                raise

def transcribe_audio_file(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: 音声ファイル '{file_path}' が見つかりません。")
        sys.exit(1)

    base_name = os.path.splitext(file_path)[0]
    print("文字起こしを開始します...")
    transcript = transcribe_audio(file_path)
    transcript_file_path = f"{base_name}_transcript.txt"
    save_text(transcript, transcript_file_path)
    print(f"文字起こし完了しました。結果は {transcript_file_path} に保存されました。")
    return transcript_file_path

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except IOError as e:
        print(f"ファイルの読み込みに失敗しました: {e}")
        raise

def save_text(text, output_file_path):
    with open(output_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(text)
        
def summarize_text_file(file_path, audio_page_url=""):
    if not os.path.exists(file_path):
        print(f"エラー: テキストファイル '{file_path}' が見つかりません。")
        sys.exit(1)
        
    print("テキストファイルを読み込んでいます...")
    transcript = read_text_file(file_path)

    base_name = os.path.splitext(file_path)[0]
    summary_file_path = f"{base_name}_summary.txt"
    print("要約を開始します...")
    summary = summarize_text(transcript, file_path)+f"\n{audio_page_url}\n"
    save_text(summary, summary_file_path)
    print(f"要約が完了しました。結果は {summary_file_path} に保存されました。")
    print("要約結果を表示します...\n\n")
    print(summary)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def post_to_x_file_path(file_path):
    try:
        # OAuth 2.0クライアントの設定
        client = get_x_client()

        # テキストファイルの内容を読み込む
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()

        # 投稿の文字数制限（280文字）を考慮
#        if len(content) > 280:
#            content = content[:277] + "..."

        # Xに投稿
#        api.update_status(content)
#        client.create_tweet(text=content)
        client.create_tweet(text="*")
        print(f"ファイル '{file_path}' の内容をXに投稿しました。")
        return True

    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
    except tweepy.errors.Forbidden as e:
        print(f"Xへの投稿中に権限エラーが発生しまし: {e}")
    except tweepy.errors.TweepyException as e:
        print(f"Xへの投稿中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

    return False


def main():
    parser = argparse.ArgumentParser(description="音声ファイルまたはテキストファイルを処理し、要約するプログラム")
    parser.add_argument("input", nargs='?', default=None, help="RSSフィードのURL、文字起こしする音声ファイル、要約するテキストファイルのいずれか。省略した場合は.envのDEFAULT_RSS_URLを使用します。")
    parser.add_argument("--singlestep", action="store_true", help="一つずつ処理を進めたい場合に指定します")
    parser.add_argument("--transcript", action="store_true", help="指定された音声ファイルから文字起こしを作成し、要約します。")
    parser.add_argument("--summarize", action="store_true", help="指定されたテキストファイル（音声書き起こし結果を想定）から要約します。")
    parser.add_argument("--post", action="store_true", help="指定されたテキストファイル（要約テキストを想定）を投稿します。(未実装)")
    args = parser.parse_args()

    if args.input is None:
        args.input = os.getenv('DEFAULT_RSS_URL')
        print(f"入力が指定されていないため、デフォルトのRSSフィードURL {args.input} を使用します。")

    if args.transcript and args.summarize:
        print("エラー: --transcript と --summarize フラグを同時に使用することはできません。")
        sys.exit(1)
        
    if args.transcript:
        transcript_file_path = transcribe_audio_file(args.input)
        if not args.singlestep:
            summarize_text_file(transcript_file_path)

    elif args.summarize:
        summarize_text_file(args.input)
        
    elif args.post:
        post_to_x_file_path(args.input)

    else:
        # RSSフィードとして処理
        audio_file_path, audio_page_url = fetch_latest_audio_from_rss(args.input)
        if not audio_file_path:
            # print("RSSフィードからの音声ファイルの取得に失敗しました。")
            sys.exit(1)

        if not args.singlestep:
            transcript_file_path = transcribe_audio_file(audio_file_path)
            summarize_text_file(transcript_file_path, audio_page_url)

if __name__ == "__main__":
    main()