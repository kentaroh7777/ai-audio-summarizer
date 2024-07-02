# AI audio summarizer

## 概要
RSSフィードから最新の音源を取得し、文字起こしと要約を行うプログラムです。

## 使い方
```bash
aitrans
```
デフォルトのstand.fmのRSSフィードから最新の音源を取得し、文字起こしと要約を行います。既に同名の音源ファイルが存在する場合、音源取得はせず、文字起こしと要約も実施されません。

```bash
aitrans https://stand.fm/rss/639bbcf87655e00c1c1430b2
```
stand.fmのRSSフィードから最新の音源を取得し、文字起こしと要約を行います。既に同名の音源ファイルが存在する場合、音源取得はせず、文字起こしと要約も実施されません。

```bash
aitrans some-audio.m4a --transcribe
```
音源ファイルから、文字起こしと要約を行います。

```bash
aitrans some-audio_trans.txt --summarize
```
テキストファイルから、要約を行います。

```bash
aitrans --singlestep
```
デフォルトのRSSフィードから音源を取得し、ファイルに保存します。ワンステップのみ実行します。既に同名の音源ファイルが存在する場合、音源取得はせず、文字起こしと要約も実施されません。

## オプション
- --singlestep ワンステップのみ実行します。
- --transcribe 音源ファイルから文字起こしと要約を行います。--singlestep が併用された場合、文字起こしのみで終了します。既に同名の音源ファイルが存在する場合、音源取得はせず、文字起こしと要約も実施されません。
- --summarize テキストファイルから要約を行います。

## セットアップ

distフォルダに実行可能形式でパッケージ化してあります。お使いのOSに応じて適宜コピーしてご利用ください。
コピーはフォルダごとコピーしてください。
例えば、macOSでは以下のようにコピーしてください。
```bash
cp -r dist/aitrans.mac /usr/local/bin/aitrans
```
コピー先の_internalフォルダの下に_env.templateをコピーし、ファイル名を.envに変更して利用ください。

### 環境設定

OpenAI（文字起こし）およびAnthropic（要約）のAPIを利用しています。.envファイルにAPIキーを設定してください。

```bash
OPENAI_API_KEY="your_openai_api_key"
ANTHROPIC_API_KEY="your_anthropic_api_key"
```

その他デフォルトのRSS URLの設定、要約のプロンプトも.envファイルに設定してください。
RSS URLはstand.fmのRSSフィードのURLを想定しています。
詳細は_env.templateを参考にしてください。