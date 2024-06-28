# AI audio summarizer

## 概要
RSSフィードから音源を取得し、文字起こしと要約を行うプログラムです。

## 使い方
```CLI
python3 aitrans.py https://stand.fm/rss/639bbcf87655e00c1c1430b2
```

stand.fmのRSSフィードから音源を取得し、文字起こしと要約を行います。

```CLI
python3 aitrans.py 20240628_PerplexityはPRO有料にしなさい565.m4a --audio

音源ファイルから、文字起こしと要約を行います。

```CLI
python3 aitrans.py 20240628_PerplexityはPRO有料にしなさい565_trans.txt --text

テキストファイルから、要約を行います。

```CLI
python3 aitrans.py https://stand.fm/rss/639bbcf87655e00c1c1430b2 --stepbystep

RSSフィードから音源を取得し、ファイルに保存します。ワンステップのみ実行します。

## オプション
- --stepbystep ワンステップのみ実行します。
- --audio 音源ファイルから文字起こしと要約を行います。
- --text テキストファイルから要約を行います。

## セットアップ

このプログラムを実行するためには、`openai`および`anthropic`モジュールをインストールする必要があります。以下のコマンドを使用してインストールしてください。

```CLI
pip install openai

```CLI
pip install anthropic

その他足りないモジュールは同様にインストールしてください。
グローバル環境にインストールできない場合は、別途pythonの仮想環境を作成し、その上でインストールしてご利用下さい。

