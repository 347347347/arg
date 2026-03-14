"""
Generate HTML pages that faithfully replicate the aberyo.or.jp design.

Design observations from the live site:
- White background, clean sans-serif (Meiryo / Hiragino)
- Header: white bg, logo left, horizontal nav with images
- Page title: large h1, then subheading text, then h1 again (WordPress style)
- Body: h2 for section headings (left-aligned, no decoration)
- Bold ◎ markers as sub-headings inside sections
- Images: displayed as block, full-width or side-by-side (2-up)
- Patient interview: h4 name, then plain paragraph text
- Footer: totop button, OUR PARTNERS logo grid, site footer nav
- Font size ~15px, generous line-height ~1.9, max-width ~860px centered
- Color: mostly black text on white, headings in dark gray/black
- NO fancy gradients or colored sidebars – very plain WordPress blog style
"""

NAV_ITEMS = [
    ("サイトトップ",             "https://aberyo.or.jp",              "m0.jpg"),
    ("毎年100人の子どもの命を救う\nプロジェクト", "https://aberyo.or.jp/hospital/", "m3.jpg"),
    ("ヒマラヤで森をつくろう\nプロジェクト",      "https://aberyo.or.jp/himalaya/",  "m6.jpg"),
    ("世界に学校を建てよう\nプロジェクト",        "https://aberyo.or.jp/schoolproject/", "m2.jpg"),
    ("ミャンマーで日本語を教えよう\nプロジェクト","https://aberyo.or.jp/japanese/",  "m7.jpg"),
    ("会長メッセージ",            "https://aberyo.or.jp/messages/",   "m1.jpg"),
    ("子どもの未来を広げる活動",   "https://aberyo.or.jp/future/",    "m5.jpg"),
]

IMG_BASE = "https://aberyo.or.jp/wp-content/themes/arz/img/"

PARTNERS = [
    ("Japan Heart",       "http://www.japanheart.org/",       "fl6_2.png"),
    ("foodbank-shibuya",  "https://foodbank-shibuya.org/",    "fl21.png"),
    ("だいじょうぶ",       "http://www.npo-daijobu.com/",      "daijoubu.png"),
    ("siab",              "https://siab.jp/",                 "fl18.png"),
    ("GMI",               "http://www.gmijp.net/",            "fl7.png"),
    ("accept",            "https://accept-int.org/",          "fl16.jpg"),
    ("ユースガーディアン", "http://ijime-sos.com/",            "fl20.png"),
    ("nikkouren",         "https://www.nikkouren.org/",       "fl19.png"),
    ("Peak Aid",          "https://peak-aid.or.jp/",          "fl10.png"),
    ("JHP・学ぶ力を支える会", "http://www.jhp.or.jp/",         "fl22.png"),
    ("アーシャ",           "http://ashaasia.org/",            "fl14.jpg"),
    ("アナコット",         "http://anacott.web.fc2.com/",     "fl17.png"),
    ("unesco",            "http://www.unesco.or.jp/saitama/","fl8.png"),
]

FOOTER_LINKS = [
    ("毎年100人の子どもの命を救うプロジェクト", "https://aberyo.or.jp/hospital/"),
    ("ヒマラヤで森をつくろうプロジェクト",       "https://aberyo.or.jp/himalaya/"),
    ("世界に学校を建てようプロジェクト",         "https://aberyo.or.jp/schoolproject/"),
    ("子どもの未来を広げる活動",                "https://aberyo.or.jp/future/"),
    ("会長 阿部 亮 メッセージ",                 "https://aberyo.or.jp/messages/"),
    ("サイトマップ",                           "https://aberyo.or.jp/sitemaps/"),
]

# Category label shown just above the main h1 (matches WordPress category/breadcrumb area)
CATEGORY_LABELS = {
    "hospital": "ジャパンハートから活動報告が届きました",
    "school":   "学校建設プロジェクトから報告が届きました",
    "japanese": "日本語教育プロジェクトから報告が届きました",
    "future":   "子どもの未来を広げる活動から報告が届きました",
}


def generate_page(sections, images, template_type, job_id):
    page_title = _get_page_title(sections)
    category_label = CATEGORY_LABELS.get(template_type, "活動報告が届きました")
    content_html = _build_content(sections, images)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(page_title)} &#8211; 一般財団法人 阿部 亮 財団</title>
{_css()}
</head>
<body>

{_header()}

<div id="wrapper">
  <div id="content">

    <div class="post-header">
      <p class="cat-label">{_esc(category_label)}</p>
      <h1 class="entry-title">{_esc(page_title)}</h1>
    </div>

    <div class="entry-content">
{content_html}
    </div><!-- .entry-content -->

  </div><!-- #content -->
</div><!-- #wrapper -->

{_footer()}

</body>
</html>"""


# ─────────────────────────────────────────────
# Content builder
# ─────────────────────────────────────────────

def _build_content(sections, images):
    parts = []
    img_idx = 0

    for section in sections:
        stype = section.get("type", "text")
        title = section.get("title", "")
        body  = section.get("body", [])

        if stype == "page_title":
            continue

        # Section heading  →  <h2>
        if title:
            if title.startswith(("◎", "【", "■", "▲", "●")):
                parts.append(f'<p><strong>{_esc(title)}</strong></p>')
            elif stype == "interview":
                parts.append(f'<h4>{_esc(title)}</h4>')
            else:
                parts.append(f'<h2>{_esc(title)}</h2>')

        # Body paragraphs – interleave images naturally
        paras = _paragraphs(body)
        for i, para in enumerate(paras):
            if para.strip():
                parts.append(f'<p>{_esc(para)}</p>')

            # Insert image(s) after every 2nd paragraph
            if (i + 1) % 2 == 0 and img_idx < len(images):
                img_idx, block = _next_image_block(images, img_idx)
                parts.append(block)

        # Insert remaining image for this section
        if img_idx < len(images) and (title or body):
            img_idx, block = _next_image_block(images, img_idx)
            parts.append(block)

    # Flush any leftover images at the end
    while img_idx < len(images):
        img_idx, block = _next_image_block(images, img_idx)
        parts.append(block)

    return "\n".join(parts)


def _next_image_block(images, idx):
    """Return (new_idx, html_block). Emit 2-up pair when two similar-sized images are adjacent."""
    remaining = len(images) - idx
    if remaining >= 2:
        # 2-up side by side (matches the site's common layout)
        a = images[idx]
        b = images[idx + 1]
        block = (
            '<div class="img-row">'
            f'<img src="{a["path"]}" alt="">'
            f'<img src="{b["path"]}" alt="">'
            '</div>'
        )
        return idx + 2, block
    else:
        img = images[idx]
        block = f'<p><img src="{img["path"]}" alt=""></p>'
        return idx + 1, block


# ─────────────────────────────────────────────
# CSS  – faithfully mirrors the live site's visual style
# ─────────────────────────────────────────────

def _css():
    return """<style>
/* ===== Reset / Base ===== */
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 15px; }
body {
  font-family: 'Hiragino Kaku Gothic ProN','Hiragino Sans','Meiryo',sans-serif;
  color: #333;
  background: #fff;
  line-height: 1.9;
}
a { color: #333; text-decoration: none; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; vertical-align: bottom; }

/* ===== Header ===== */
#header {
  background: #fff;
  border-bottom: 1px solid #ddd;
}
#header .inner {
  max-width: 980px;
  margin: 0 auto;
  padding: 14px 20px 0;
}
#header .site-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}
#header .site-title a { color: #666; }

/* Global nav – horizontal image tiles */
#gnav {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-top: 1px solid #e0e0e0;
}
#gnav > li { flex: 1; min-width: 120px; }
#gnav > li > a {
  display: block;
  text-align: center;
  font-size: 11px;
  line-height: 1.4;
  color: #333;
  padding: 6px 4px 8px;
  border-right: 1px solid #e0e0e0;
  background: #fafafa;
  white-space: pre-line;
}
#gnav > li > a:hover { background: #f0f0f0; text-decoration: none; }
#gnav > li > a img {
  display: block;
  width: 100%;
  height: 54px;
  object-fit: cover;
  margin-bottom: 4px;
}

/* ===== Main wrapper ===== */
#wrapper {
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

/* ===== Post header ===== */
.post-header {
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ddd;
}
.post-header .cat-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}
.post-header .entry-title {
  font-size: 24px;
  font-weight: bold;
  line-height: 1.5;
  color: #222;
}

/* ===== Entry content ===== */
.entry-content h2 {
  font-size: 18px;
  font-weight: bold;
  color: #222;
  margin: 32px 0 12px;
  padding-bottom: 6px;
  border-bottom: 2px solid #333;
}
.entry-content h4 {
  font-size: 15px;
  font-weight: bold;
  color: #333;
  margin: 24px 0 6px;
}
.entry-content p {
  margin-bottom: 14px;
  text-align: justify;
}
.entry-content p strong {
  font-weight: bold;
}

/* Images: single full-width */
.entry-content p img {
  display: block;
  width: 100%;
  max-width: 640px;
  height: auto;
  margin: 8px 0 16px;
}

/* Images: 2-up side by side (matches site layout) */
.entry-content .img-row {
  display: flex;
  gap: 8px;
  margin: 12px 0 20px;
}
.entry-content .img-row img {
  flex: 1;
  width: 0;          /* flex child trick */
  height: 220px;
  object-fit: cover;
}

/* ===== totop button ===== */
#totop {
  text-align: right;
  margin: 40px 0 20px;
}
#totop a img { width: 60px; }

/* ===== OUR PARTNERS ===== */
#partners {
  background: #f5f5f5;
  padding: 28px 24px;
  margin-top: 20px;
}
#partners h3 {
  font-size: 13px;
  font-weight: bold;
  color: #555;
  letter-spacing: 0.15em;
  margin-bottom: 16px;
  text-align: center;
}
#partners .partner-sub {
  font-size: 12px;
  color: #777;
  text-align: center;
  margin-bottom: 14px;
}
#partners ul {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px 20px;
}
#partners ul li a img {
  height: 36px;
  width: auto;
  object-fit: contain;
  filter: grayscale(30%);
  opacity: 0.85;
}
#partners ul li a:hover img { opacity: 1; filter: none; }

/* ===== Footer ===== */
#footer {
  background: #fff;
  border-top: 1px solid #ddd;
  padding: 20px 24px 32px;
  text-align: center;
}
#footer .footer-logo {
  margin-bottom: 14px;
}
#footer .footer-logo img { height: 50px; width: auto; }
#footer nav ul {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px 20px;
  margin-bottom: 14px;
}
#footer nav ul li a {
  font-size: 12px;
  color: #666;
}
#footer nav ul li a:hover { text-decoration: underline; }
#footer .copyright {
  font-size: 12px;
  color: #aaa;
}

/* ===== Responsive ===== */
@media (max-width: 640px) {
  #gnav > li { min-width: 80px; }
  #gnav > li > a { font-size: 10px; }
  #wrapper { padding: 20px 14px 40px; }
  .post-header .entry-title { font-size: 19px; }
  .entry-content .img-row { flex-direction: column; }
  .entry-content .img-row img { width: 100%; height: auto; }
}
</style>"""


# ─────────────────────────────────────────────
# Header HTML
# ─────────────────────────────────────────────

def _header():
    nav_items_html = "\n".join(
        f'<li><a href="{href}">'
        f'<img src="{IMG_BASE}{img}" alt="{_esc(label)}">'
        f'{_esc(label)}</a></li>'
        for label, href, img in NAV_ITEMS
    )
    return f"""<div id="header">
  <div class="inner">
    <p class="site-title">
      <a href="https://aberyo.or.jp">一般財団法人 阿部 亮 財団 - ABE RYO FOUNDATION -</a>
    </p>
    <ul id="gnav">
{nav_items_html}
    </ul>
  </div>
</div>"""


# ─────────────────────────────────────────────
# Footer HTML
# ─────────────────────────────────────────────

def _footer():
    partners_html = "\n".join(
        f'<li><a href="{href}" target="_blank" rel="noopener">'
        f'<img src="{IMG_BASE}{img}" alt="{_esc(name)}"></a></li>'
        for name, href, img in PARTNERS
    )
    footer_nav_html = "\n".join(
        f'<li><a href="{href}">{_esc(label)}</a></li>'
        for label, href in FOOTER_LINKS
    )
    return f"""<div id="totop">
  <a href="#"><img src="{IMG_BASE}totop.jpg" alt="topへ"></a>
</div>

<div id="partners">
  <h3>OUR PARTNERS</h3>
  <p class="partner-sub">阿部 亮 財団は 下記の団体の活動を支援しています</p>
  <ul>
{partners_html}
  </ul>
</div>

<div id="footer">
  <div class="footer-logo">
    <img src="{IMG_BASE}logo.png" alt="一般財団法人 阿部 亮 財団">
  </div>
  <nav>
    <ul>
{footer_nav_html}
    </ul>
  </nav>
  <p class="copyright">©Abe Ryo Foundation</p>
</div>"""


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_page_title(sections):
    for s in sections:
        if s.get("type") == "page_title" and s.get("title"):
            return s["title"]
    for s in sections:
        if s.get("title"):
            return s["title"]
    return "活動レポート"


def _paragraphs(lines):
    """Merge lines into natural paragraphs."""
    if not lines:
        return []
    result, buf = [], []
    for line in lines:
        line = line.strip()
        if not line:
            if buf:
                result.append(" ".join(buf))
                buf = []
        elif line.endswith("。") or len(line) > 100:
            buf.append(line)
            result.append(" ".join(buf))
            buf = []
        else:
            buf.append(line)
    if buf:
        result.append(" ".join(buf))
    return [p for p in result if p.strip()]


def _esc(text):
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))
