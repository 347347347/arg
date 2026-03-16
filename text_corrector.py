"""
text_corrector.py
PDF抽出テキストの修正を2段階で行う。

Step 1 (Python正規表現): 不自然な空白を確実・即時に除去
Step 2 (Claude API):     文字化け・誤字脱字・残った不自然な表現を修正
"""

import json
import urllib.request
import os
import re


# ─────────────────────────────────────────────────────────
# Step 1: 正規表現による空白除去（API不要・確実）
# ─────────────────────────────────────────────────────────

def fix_pdf_spaces(text: str) -> str:
    """PDFから抽出したテキストの不自然な空白を除去する。"""

    # 0. 全角スペース(\u3000)を半角スペースに統一
    text = text.replace('\u3000', ' ')

    # 1. 日本語文字(ひらがな・カタカナ・漢字・記号)の間の半角スペースを除去
    #    「ボラン ティア」→「ボランティア」 / 「活 動 報 告」→「活動報告」
    JP = r'[\u3000-\u9fff\uff00-\uffef]'
    for _ in range(8):  # 「活 動 報 告」のように連続する場合を繰り返し除去
        new = re.sub(rf'({JP}) ({JP})', r'\1\2', text)
        if new == text:
            break
        text = new

    # 2. 日本語文字とASCII英数字の間の不自然なスペースを除去
    #    「Japan Heart医 療センター」→「Japan Heart医療センター」
    text = re.sub(rf'({JP}) ([a-zA-Z0-9])', r'\1\2', text)
    text = re.sub(rf'([a-zA-Z0-9]) ({JP})', r'\1\2', text)

    # 3. 日本語記号の前後スペース除去
    #    「認定医 ・堀」→「認定医・堀」 / 「・ 堀医師」→「・堀医師」
    SYMBOLS = r'[・。、！？：；「」『』【】〔〕（）…—〇]'
    text = re.sub(rf' ({SYMBOLS})', r'\1', text)
    text = re.sub(rf'({SYMBOLS}) ', r'\1', text)

    # 4. 数字と助数詞の間のスペース除去
    #    「1 月」→「1月」 / 「18 件」→「18件」 / 「10 日」→「10日」
    COUNTERS = r'[月日年時分秒件回人名校棟冊枚台個万円ページ週]'
    text = re.sub(rf'(\d) ({COUNTERS})', r'\1\2', text)

    # 5. 数字と年号助詞の間 (「2026 年」→「2026年」)
    text = re.sub(r'(\d) (年|月|日|時|分|秒)', r'\1\2', text)

    # 6. 波ダッシュ・チルダ前後のスペース
    #    「1月 10 ～ 13 日」→「1月10～13日」
    text = re.sub(r' ?[～〜] ?', '～', text)
    # ただし数字同士の間でない場合は半角スペースを復元しない（英文中など）
    # → 数字間のみ結合（上のルールで十分）

    # 7. 連続スペースを1つに
    text = re.sub(r'  +', ' ', text)

    # 8. 行頭・行末スペース除去
    return text.strip()


def fix_sections_spaces(sections: list) -> list:
    """sectionsリスト全体に空白修正を適用する。"""
    result = []
    for section in sections:
        s = dict(section)
        if s.get('title'):
            s['title'] = fix_pdf_spaces(s['title'])
        if s.get('body'):
            s['body'] = [fix_pdf_spaces(line) for line in s['body']]
        result.append(s)
    return result


# ─────────────────────────────────────────────────────────
# Step 2: Claude APIによる誤字脱字・文字化け修正
# ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """あなたはNPO・財団の活動報告ブログ編集者です。
PDFから抽出・前処理済みのテキストの校正を行います。

【修正すること】
1. 文字化け（例：縺ｦ縺�→て / ??→適切な文字）
2. 明らかな誤字脱字（例：「実しました」→「実施しました」）
3. 残っている不自然な空白・文字の結合ミス
4. 行末の不自然な句読点

【絶対に変えないこと】
1. 内容・意味・事実
2. 文体・口調
3. 固有名詞（人名・地名・団体名）
4. 意図的な改行・段落構成

【出力形式】JSONのみ。前置き・後書き・```不要。
{
  "title": "修正後のページタイトル",
  "sections": [
    {
      "type": "page_title|section|text|interview",
      "title": "見出し（なければ空文字）",
      "body": ["段落1", "段落2"]
    }
  ]
}"""


def correct_text(sections: list, template_type: str) -> list:
    """
    Step1: 正規表現で空白を即時修正
    Step2: Claude APIで文字化け・誤字脱字を修正（APIなければStep1結果を返す）
    """
    if not sections:
        return sections

    # Step 1: 必ず実行（API不要・高速）
    sections = fix_sections_spaces(sections)

    # Step 2: Claude API（環境変数にキーがある場合のみ）
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return sections

    input_data = json.dumps(sections, ensure_ascii=False, separators=(',', ':'))
    user_prompt = (
        f"以下はPDFから抽出した「{_template_label(template_type)}」の活動報告テキストです。"
        f"文字化け・誤字脱字を修正してください。\n\n{input_data}"
    )

    try:
        raw = _call_claude_api(api_key, user_prompt)
        corrected = _parse_response(raw)
        if corrected:
            # API結果にも空白修正を再適用（念のため）
            return fix_sections_spaces(corrected)
    except Exception as e:
        print(f"[text_corrector] API error (using Step1 result): {e}")

    return sections


# ─────────────────────────────────────────────────────────
# 内部ヘルパー
# ─────────────────────────────────────────────────────────

def _call_claude_api(api_key: str, user_prompt: str) -> str:
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    for block in body.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""


def _parse_response(text: str) -> list:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
            except Exception:
                return []
        else:
            return []

    if isinstance(data, dict) and "sections" in data:
        sections = data["sections"]
        if data.get("title"):
            sections = [s for s in sections if s.get("type") != "page_title"]
            sections.insert(0, {"type": "page_title", "title": data["title"], "body": []})
        return sections

    if isinstance(data, list):
        return data

    return []


def _template_label(t: str) -> str:
    return {
        "hospital": "病院・医療活動",
        "school":   "学校建設プロジェクト",
        "japanese": "日本語教育プロジェクト",
        "future":   "子どもの未来活動",
    }.get(t, "活動報告")
