"""
text_corrector.py
Claude APIを使ってPDF抽出テキストの文字化け・誤字脱字・空白を自動修正する。
"""

import json
import urllib.request
import urllib.error
import os
import re


SYSTEM_PROMPT = """あなたはNPO・財団の活動報告ブログ編集者です。
PDFから抽出したテキストの校正を行います。

以下のルールに従って修正してください：

【修正すること】
1. 文字化け（例：縺ｦ縺�→ て、 / ??→適切な文字）の修正
2. 明らかな誤字脱字の修正（例：「実しました」→「実施しました」）
3. 不自然な空白・改行の除去（単語の途中の空白、全角スペースの連続など）
4. 数字・記号の正規化（半角/全角の統一、「①」→「1.」など文脈に合わせた修正）
5. 行末の不自然な句読点の修正
6. PDF抽出時に分割された単語の結合（例：「実 施」→「実施」）

【修正しないこと】
1. 内容・意味の変更
2. 文体・口調の変更
3. 固有名詞（人名・地名・団体名）の勝手な変更
4. 意図的と思われる改行・段落分け

【出力形式】
必ずJSON形式のみで返してください。前置き・後書き・マークダウン不要。
{
  "title": "修正後のページタイトル",
  "sections": [
    {
      "type": "page_title" または "section" または "text" または "interview",
      "title": "セクション見出し（なければ空文字）",
      "body": ["段落1", "段落2", ...]
    }
  ]
}
"""


def correct_text(sections: list, template_type: str) -> list:
    """
    Claude APIでsectionsのテキストを校正して返す。
    APIが使えない場合はsectionsをそのまま返す（フォールバック）。
    """
    if not sections:
        return sections

    # 入力をコンパクトなJSONに変換
    input_data = json.dumps(sections, ensure_ascii=False, separators=(',', ':'))

    user_prompt = f"""以下はPDFから抽出した「{_template_label(template_type)}」の活動報告テキストです。
文字化け・誤字脱字・不自然な空白を修正してください。

{input_data}"""

    try:
        result = _call_claude_api(user_prompt)
        corrected = _parse_response(result)
        if corrected:
            return corrected
    except Exception as e:
        print(f"[text_corrector] API error (fallback to original): {e}")

    return sections


def _call_claude_api(user_prompt: str) -> str:
    """Claude API /v1/messages を呼び出す。"""
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            # APIキーは環境変数から取得（Railway Variables に設定）
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    # content[0].text を取り出す
    for block in body.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""


def _parse_response(text: str) -> list:
    """APIレスポンスからsectionsリストを抽出する。"""
    if not text:
        return []

    # マークダウンコードブロックを除去
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 部分的なJSONを探して抽出を試みる
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
            except Exception:
                return []
        else:
            return []

    # "sections" キーがあればそれを使う
    if isinstance(data, dict) and "sections" in data:
        sections = data["sections"]
        # page_title を先頭に追加（titleフィールドがあれば）
        if "title" in data and data["title"]:
            page_title_section = {
                "type": "page_title",
                "title": data["title"],
                "body": []
            }
            # 既存のpage_titleを置き換え
            sections = [s for s in sections if s.get("type") != "page_title"]
            sections.insert(0, page_title_section)
        return sections

    # sectionsリストが直接返ってきた場合
    if isinstance(data, list):
        return data

    return []


def _template_label(template_type: str) -> str:
    return {
        "hospital": "病院・医療活動",
        "school":   "学校建設プロジェクト",
        "japanese": "日本語教育プロジェクト",
        "future":   "子どもの未来活動",
    }.get(template_type, "活動報告")
