# ARG ブログページ自動生成ツール
## 一般財団法人 阿部 亮 財団 — PDF → ブログページ変換

PDFをアップロードすると、財団の4種類のブログテンプレートに合わせたHTMLページを自動生成します。

---

## 機能

- PDFからテキスト・画像を自動抽出
- 写真を最適なサイズ・縦横比にスマートトリミング
- 4テンプレート対応：
  - 🏥 病院ページ（毎年100人の子どもの命を救うプロジェクト）
  - 🏫 学校ページ（世界に学校を建てようプロジェクト）
  - 🇯🇵 日本語ページ（ミャンマーで日本語を教えようプロジェクト）
  - 🌟 未来ページ（子どもの未来を広げる活動）
- プレビュー確認
- HTML + 画像ファイルをZIPでダウンロード

---

## ローカル開発

```bash
# 依存パッケージのインストール（poppler必須）
# macOS: brew install poppler
# Ubuntu: apt-get install poppler-utils

pip install -r requirements.txt
python app.py
# → http://localhost:5000 で起動
```

---

## GitHubへのプッシュ

```bash
cd aberyo-blog-generator

git init
git add .
git commit -m "Initial commit: ARG blog generator"

# GitHubでリポジトリ作成後:
git remote add origin https://github.com/YOUR_USERNAME/aberyo-blog-generator.git
git branch -M main
git push -u origin main
```

---

## Railwayへのデプロイ

### 方法1: GitHub連携（推奨）

1. [railway.app](https://railway.app) にログイン
2. 「New Project」→「Deploy from GitHub repo」
3. `aberyo-blog-generator` リポジトリを選択
4. 自動でビルド・デプロイが始まります

### 方法2: Railway CLI

```bash
# Railway CLIをインストール
npm install -g @railway/cli

# ログイン
railway login

# プロジェクト作成・デプロイ
railway init
railway up
```

### 環境変数（Railway Dashboard > Variables）

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `PORT` | 自動設定 | Railwayが自動で設定 |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Claude APIキー（テキスト校正に使用）|

> **ANTHROPIC_API_KEY の取得方法**  
> [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key

---

## ファイル構成

```
aberyo-blog-generator/
├── app.py              # Flaskアプリ本体
├── pdf_processor.py    # PDF処理（テキスト・画像抽出）
├── page_generator.py   # HTMLページ生成（4テンプレート）
├── templates/
│   └── index.html      # 操作UI
├── requirements.txt    # Pythonパッケージ
├── Procfile            # Railway/Heroku用
├── nixpacks.toml       # Railway Nixpacksビルド設定
├── railway.toml        # Railwayデプロイ設定
└── .gitignore
```

---

## 技術スタック

- **Backend**: Python / Flask
- **PDF処理**: pypdf, pdf2image (poppler), pdfminer.six
- **画像処理**: Pillow (PIL)
- **デプロイ**: Railway + Gunicorn

---

©Abe Ryo Foundation — Internal Tool
