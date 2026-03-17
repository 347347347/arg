"""
text_corrector.py
PDF抽出テキストの修正を2段階で行う。

Step 1 (Python): レイアウト型PDFの行末改行を結合 + 不自然な空白を除去
Step 2 (Claude API): 残った文字化け・誤字脱字を修正
"""

import json
import urllib.request
import os
import re


# ─────────────────────────────────────────────────────────
# Step 1-A: 行末改行の結合（レイアウト型PDFの主な問題）
# ─────────────────────────────────────────────────────────

# 文の終わりと判断する文字
SENTENCE_END = set('。．！？」』）〕')

# 見出し行と判断するパターン（◎●■で始まる、または短い行）
HEADING_LINE = re.compile(r'^[◎●■▲★【〔*＊]')

# 段落・ブロック開始と判断するパターン（次の行がこれなら結合しない）
BLOCK_START = re.compile(r'^[◎●■▲★【〔*＊]|^\d+[\.．]')

# 途中で切れている行末（結合すべき）― 日本語文字・読点で終わる
MID_SENTENCE_END = re.compile(r'[\u3040-\u9fff\uff00-\uffef、・]$')


def join_broken_lines(text: str) -> str:
    """
    レイアウト型PDFで行末強制改行されたテキストを結合する。
    ルール：
      - 見出し行（◎等で始まる行）は結合の起点にしない → 改行を保持
      - 次の行が見出し・空行 → 改行を保持
      - 行末が「。」等文末 → 改行を保持
      - 行末が日本語文字・読点（途中で切れている） → 次の行と結合
    """
    # \u2028（行区切り文字）を改行に統一
    text = text.replace('\u2028', '\n')

    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        # 空行はそのまま保持（段落区切り）
        if not stripped:
            result.append('')
            i += 1
            continue

        # ── 見出し行は結合の起点にしない ──
        # 「◎短期ボランティア受け入れ再開」のような行はそのまま出力
        if HEADING_LINE.match(stripped):
            result.append(line)
            i += 1
            continue

        last_char = stripped[-1]

        # 次の行を確認
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ''

        # 次の行が見出し・空行 → 結合しない
        next_is_new_block = (
            not next_stripped
            or bool(BLOCK_START.match(next_stripped))
        )

        # 行末が文の終わり → 結合しない
        if last_char in SENTENCE_END or next_is_new_block:
            result.append(line)
            i += 1
            continue

        # 行末が途中（日本語文字・読点） → 次の行と結合
        if MID_SENTENCE_END.search(stripped):
            merged = stripped
            while i + 1 < len(lines):
                next_l = lines[i + 1].rstrip()
                next_s = next_l.strip()
                # 空行 or 新ブロック（見出し等） → 結合終了
                if not next_s or bool(BLOCK_START.match(next_s)):
                    break
                merged += next_s
                i += 1
                # 文末に達したら終了
                if merged[-1] in SENTENCE_END:
                    break
            result.append(merged)
            i += 1
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


# ─────────────────────────────────────────────────────────
# Step 1-B: 残存する不自然な空白の除去
# ─────────────────────────────────────────────────────────

JP = r'[\u3040-\u9fff\uff00-\uffef]'


def fix_spaces(text: str) -> str:
    """日本語文字間・記号前後の不自然なスペースを除去する。"""
    text = text.replace('\u3000', ' ')

    for _ in range(8):
        new = re.sub(rf'({JP}) ({JP})', r'\1\2', text)
        if new == text:
            break
        text = new

    text = re.sub(rf'({JP}) ([a-zA-Z0-9])', r'\1\2', text)
    text = re.sub(rf'([a-zA-Z0-9]) ({JP})', r'\1\2', text)

    SYMS = r'[・。、！？：；「」『』【】〔〕（）…—〇]'
    text = re.sub(rf' ({SYMS})', r'\1', text)
    text = re.sub(rf'({SYMS}) ', r'\1', text)

    text = re.sub(r'(\d) ([月日年時分秒件回人名校棟冊枚台個万円週])', r'\1\2', text)
    text = re.sub(r'  +', ' ', text)

    return text.strip()


def fix_sections_spaces(sections: list) -> list:
    fixed = []
    for s in sections:
        sc = dict(s)
        if sc.get('title'):
            sc['title'] = fix_spaces(sc['title'])
        if sc.get('body'):
            sc['body'] = [fix_spaces(l) for l in sc['body']]
        fixed.append(sc)
    return fixed


# ─────────────────────────────────────────────────────────
# メイン前処理（extract_text の直後に呼ぶ）
# ─────────────────────────────────────────────────────────

def preprocess_text(raw_text: str) -> str:
    """PDFから抽出した生テキストに行結合＋空白除去を適用する。"""
    text = join_broken_lines(raw_text)
    text = fix_spaces(text)
    return text


# ─────────────────────────────────────────────────────────
# Step 2: Claude API（誤字脱字・文字化けの修正）
# ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """あなたはNPO・財団の活動報告ブログ編集者です。
PDFから抽出・前処理済みのテキストの校正を行います。

【修正すること】
1. 文字化け（例：縺ｦ縺乗て）
2. 明らかな誤字脱字（例：「実しました」→「実施しました」）
3. 残っている不自然な文字結合・分断

【絶対に変えないこと】
1. 内容・意味・事実・数字
2. 文体・口調
3. 固有名詞（人名・地名・団体名）
4. 段落構成・改行

【出力形式】JSONのみ。```不要。
{
  "title": "ページタイトル",
  "sections": [
    {"type": "page_title|section|text|interview", "title": "見出し", "body": ["段落1", "段落2"]}
  ]
}"""


def correct_text(sections: list, template_type: str) -> list:
    """Step1で空白・改行を修正済みのsectionsをAPIでさらに校正する。"""
    if not sections:
        return sections

    sections = fix_sections_spaces(sections)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return sections

    input_data = json.dumps(sections, ensure_ascii=False, separators=(',', ':'))
    user_prompt = (
        f"以下はPDFから抽出した「{_label(template_type)}」の活動報告テキストです。"
        f"文字化け・誤字脱字を修正してください。\n\n{input_data}"
    )

    try:
        raw = _call_api(api_key, user_prompt)
        corrected = _parse(raw)
        if corrected:
            return fix_sections_spaces(corrected)
    except Exception as e:
        print(f"[text_corrector] API error (Step1 result used): {e}")

    return sections


# ─────────────────────────────────────────────────────────
# 内部ヘルパー
# ─────────────────────────────────────────────────────────

def _call_api(api_key: str, prompt: str) -> str:
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}]
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


def _parse(text: str) -> list:
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
        secs = data["sections"]
        if data.get("title"):
            secs = [s for s in secs if s.get("type") != "page_title"]
            secs.insert(0, {"type": "page_title", "title": data["title"], "body": []})
        return secs
    if isinstance(data, list):
        return data
    return []


def _label(t: str) -> str:
    return {
        "hospital": "病院・医療活動",
        "school":   "学校建設プロジェクト",
        "japanese": "日本語教育プロジェクト",
        "future":   "子どもの未来活動",
    }.get(t, "活動報告")
