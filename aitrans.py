import os
import sys
import argparse
import time
from openai import OpenAI
from openai import RateLimitError, APIError
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# 音声ファイルを取得するRSSフィードのURL
RSS_URL = "https://stand.fm/rss/639bbcf87655e00c1c1430b2"
# 環境変数からAPIキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

if not openai_api_key:
    print("エラー: OPENAI_API_KEY 環境変数が設定されていません。")
    sys.exit(1)
if not anthropic_api_key:
    print("エラー: ANTHROPIC_API_KEY 環境変数が設定されていません。")
    sys.exit(1)

# OpenAI クライアントの初期化
openai_client = OpenAI(api_key=openai_api_key)
# Anthropic クライアントの初期化
anthropic_client = Anthropic(api_key=anthropic_api_key)

import feedparser
import requests
import os
from datetime import datetime

def fetch_latest_audio_from_rss(rss_url):
    # RSSフィードを解析
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("フィードにエントリーがありません���")
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

    # ファイル名を生成（日付_タイトル.mp3）
    date_str = datetime.now().strftime("%Y%m%d")
    title = latest_entry.title
    # ファイル名に使用できない文字を除去
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{date_str}_{safe_title}.m4a"

    # 音声ファイルをダウンロード
    print(f"最新エピソード「{title}」をダウンロードしています...")
    response = requests.get(audio_url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        print(f"ダウンロード完了: {filename}")
        return filename
    else:
        print("ダウンロードに失敗しました。")
        return None


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
    prompt = read_prompt('prompt-summarize.txt')
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

def process_audio_file(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: 音声ファイル '{file_path}' が見つかりません。")
        sys.exit(1)

    base_name = os.path.splitext(file_path)[0]
    print("文字起こしを開始します...")
    transcript = transcribe_audio(file_path)
    transcript_file_path = f"{base_name}_transcript.txt"
    save_text(transcript, transcript_file_path)
    print(f"文字起こしが完了しました。結果は {transcript_file_path} に保存されました。")
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
        
def process_text_file(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: テキストファイル '{file_path}' が見つかりません。")
        sys.exit(1)
        
    print("テキストファイルを読み込んでいます...")
    transcript = read_text_file(file_path)

    base_name = os.path.splitext(file_path)[0]
    summary_file_path = f"{base_name}_summary.txt"
    print("要約を開始します...")
    summary = summarize_text(transcript, file_path)
    save_text(summary, summary_file_path)
    print(f"要約が完了しました。結果は {summary_file_path} に保存されました。")

def main():
    parser = argparse.ArgumentParser(description="音声ファイルまたはテキストファイルを処理し、要約するプログラム")
    parser.add_argument("input", help="RSSフィードのURL、文字起こしする音声ファイル、要約するテキストファイルのいずれか）")
    parser.add_argument("--stepbystep", action="store_true", help="一つずつ処理を進めたい場合に指定する")
    parser.add_argument("--text", action="store_true", help="入力がテキストファイルの場合はこのフラグを使用。テキストファイルから要約を作成します。")
    parser.add_argument("--audio", action="store_true", help="入力が音声ファイルの場合はこのフラグを使用。音声ファイルから文字起こしを作成し要約を作成します。")
    args = parser.parse_args()

#    if not os.path.exists(args.input):
#        print(f"エラー: インプット '{args.input}' が見つかりません。")
#        sys.exit(1)
        
    if args.audio and args.text:
        print("エラー: --audio と --text フラグを同時に使用することはできません。")
        sys.exit(1)
        
    if args.audio:
        transcript_file_path = process_audio_file(args.input)
        if not args.stepbystep:
            process_text_file(transcript_file_path)

    elif args.text:
        process_text_file(args.input)

    else:
        # RSSフィードとして処理
        audio_file_path = fetch_latest_audio_from_rss(args.input)
        if not audio_file_path:
            print("RSSフィードからの音声ファイルの取得に失敗しました。")
            sys.exit(1)

        if not args.stepbystep:
            transcript_file_path = process_audio_file(audio_file_path)
            process_text_file(transcript_file_path)

if __name__ == "__main__":
    main()