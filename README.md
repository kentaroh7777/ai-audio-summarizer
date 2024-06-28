# AI audio summarizer

## 概要
RSSフィードから最新の音源を取得し、文字起こしと要約を行うプログラムです。

## 使い方
```bash
python3 aitrans.py https://stand.fm/rss/639bbcf87655e00c1c1430b2
```
stand.fmのRSSフィードから最新の音源を取得し、文字起こしと要約を行います。

```bash
python3 aitrans.py 20240628_PerplexityはPRO有料にしなさい565.m4a --audio
```
音源ファイルから、文字起こしと要約を行います。

```bash
python3 aitrans.py 20240628_PerplexityはPRO有料にしなさい565_trans.txt --text
```
テキストファイルから、要約を行います。

```bash
python3 aitrans.py https://stand.fm/rss/639bbcf87655e00c1c1430b2 --stepbystep
```
RSSフィードから音源を取得し、ファイルに保存します。ワンステップのみ実行します。

## オプション
- --stepbystep ワンステップのみ実行します。
- --audio 音源ファイルから文字起こしと要約を行います。--stepbystep が併用された場合、文字起こしのみで終了します。
- --text テキストファイルから要約を行います。

## セットアップ

### 環境設定

このプログラムを実行するためには、`openai`および`anthropic`モジュールをインストールする必要があります。以下のコマンドを使用してインストールしてください。

```bash
pip install openai
pip install anthropic
```

その他足りないモジュールは同様にインストールしてください。
グローバル環境にインストールできない場合は、別途pythonの仮想環境を作成し、その上でインストールしてご利用下さい。

OpenAI（文字起こし）およびAnthropic（要約）のAPIを利用しています。以下の環境変数にAPIキーを設定してください。

```bash
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 要約のプロンプト

prompt-summarize.txt に文字起こしから要約のためのプロンプトを設定してください。初期状態にサンプルが入っていますので、自由に変更して利用してください。