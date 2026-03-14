"""Generate HTML pages based on ARG blog templates."""

TEMPLATE_COLORS = {
    'hospital': {
        'primary': '#2a6496',
        'secondary': '#e8f4f8',
        'accent': '#5bc0de',
        'header_bg': '#1a4a6e',
        'label': '病院レポート',
        'category': '毎年100人の子どもの命を救うプロジェクト',
    },
    'school': {
        'primary': '#3a7a3a',
        'secondary': '#e8f5e8',
        'accent': '#5cb85c',
        'header_bg': '#2a5a2a',
        'label': '学校レポート',
        'category': '世界に学校を建てようプロジェクト',
    },
    'japanese': {
        'primary': '#8b4513',
        'secondary': '#fdf5e6',
        'accent': '#cd853f',
        'header_bg': '#6b3410',
        'label': '日本語教育レポート',
        'category': 'ミャンマーで日本語を教えようプロジェクト',
    },
    'future': {
        'primary': '#6a0dad',
        'secondary': '#f5e8ff',
        'accent': '#9b59b6',
        'header_bg': '#4a0080',
        'label': '未来活動レポート',
        'category': '子どもの未来を広げる活動',
    },
}

def generate_page(sections, images, template_type, job_id):
    """Generate complete HTML page."""
    colors = TEMPLATE_COLORS.get(template_type, TEMPLATE_COLORS['hospital'])
    
    # Extract page title
    page_title = 'ARG活動レポート'
    for s in sections:
        if s.get('type') == 'page_title' and s.get('title'):
            page_title = s['title']
            break
        elif s.get('title'):
            page_title = s['title']
            break
    
    # Build content blocks
    content_html = build_content(sections, images, template_type)
    
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(page_title)} | 一般財団法人 阿部 亮 財団</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'Meiryo', sans-serif;
    color: #333;
    background: #fff;
    line-height: 1.8;
    font-size: 15px;
  }}
  
  /* Header */
  .site-header {{
    background: {colors['header_bg']};
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .site-header .logo {{
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    text-decoration: none;
    letter-spacing: 0.05em;
  }}
  .site-header .logo span {{
    font-size: 12px;
    display: block;
    opacity: 0.8;
    font-weight: normal;
  }}
  
  /* Category bar */
  .category-bar {{
    background: {colors['primary']};
    color: #fff;
    font-size: 13px;
    padding: 8px 20px;
    letter-spacing: 0.08em;
  }}
  
  /* Page wrapper */
  .page-wrapper {{
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 20px 60px;
  }}
  
  /* Page title */
  .page-title-block {{
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 3px solid {colors['primary']};
  }}
  .label-tag {{
    display: inline-block;
    background: {colors['primary']};
    color: #fff;
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 2px;
    margin-bottom: 10px;
    letter-spacing: 0.05em;
  }}
  .page-title {{
    font-size: 26px;
    font-weight: bold;
    color: {colors['primary']};
    line-height: 1.4;
  }}
  
  /* Hero image */
  .hero-image {{
    width: 100%;
    max-height: 480px;
    object-fit: cover;
    border-radius: 4px;
    margin-bottom: 32px;
    display: block;
  }}
  
  /* Section */
  .section-block {{
    margin-bottom: 40px;
  }}
  .section-heading {{
    font-size: 19px;
    font-weight: bold;
    color: {colors['primary']};
    border-left: 5px solid {colors['accent']};
    padding: 6px 0 6px 14px;
    margin-bottom: 16px;
    background: {colors['secondary']};
    border-radius: 0 3px 3px 0;
  }}
  .section-subheading {{
    font-size: 16px;
    font-weight: bold;
    color: #444;
    margin: 20px 0 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid #ddd;
  }}
  .section-text {{
    color: #444;
    margin-bottom: 14px;
    text-align: justify;
  }}
  
  /* Image layouts */
  .img-single {{
    width: 100%;
    margin: 20px 0;
  }}
  .img-single img {{
    width: 100%;
    height: auto;
    max-height: 480px;
    object-fit: cover;
    border-radius: 4px;
    display: block;
  }}
  .img-caption {{
    font-size: 13px;
    color: #666;
    text-align: center;
    margin-top: 6px;
    font-style: italic;
  }}
  .img-pair {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 20px 0;
  }}
  .img-pair img {{
    width: 100%;
    height: 220px;
    object-fit: cover;
    border-radius: 4px;
  }}
  .img-trio {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin: 20px 0;
  }}
  .img-trio img {{
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 4px;
  }}
  
  /* Patient/Profile card */
  .profile-card {{
    background: {colors['secondary']};
    border: 1px solid {colors['accent']}44;
    border-radius: 6px;
    padding: 20px;
    margin: 20px 0;
    display: flex;
    gap: 20px;
    align-items: flex-start;
  }}
  .profile-card img {{
    width: 140px;
    height: 140px;
    object-fit: cover;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  .profile-info h4 {{
    font-size: 16px;
    color: {colors['primary']};
    margin-bottom: 8px;
  }}
  .profile-info p {{
    font-size: 14px;
    color: #555;
    line-height: 1.7;
  }}
  
  /* Highlight box */
  .highlight-box {{
    background: {colors['secondary']};
    border-left: 4px solid {colors['primary']};
    padding: 16px 20px;
    margin: 20px 0;
    border-radius: 0 4px 4px 0;
    font-size: 14px;
    color: #444;
  }}
  
  /* Footer */
  .page-footer {{
    margin-top: 60px;
    padding-top: 30px;
    border-top: 2px solid {colors['primary']};
    text-align: center;
    color: #888;
    font-size: 13px;
  }}
  .page-footer .footer-logo {{
    font-size: 16px;
    font-weight: bold;
    color: {colors['primary']};
    margin-bottom: 8px;
  }}
  
  /* Responsive */
  @media (max-width: 600px) {{
    .img-pair {{ grid-template-columns: 1fr; }}
    .img-trio {{ grid-template-columns: 1fr 1fr; }}
    .profile-card {{ flex-direction: column; }}
    .profile-card img {{ width: 100%; height: 200px; }}
    .page-title {{ font-size: 20px; }}
  }}
</style>
</head>
<body>

<header class="site-header">
  <a href="https://aberyo.or.jp" class="logo">
    一般財団法人 阿部 亮 財団
    <span>ABE RYO FOUNDATION</span>
  </a>
</header>

<div class="category-bar">
  {colors['category']}
</div>

<div class="page-wrapper">

  <div class="page-title-block">
    <div class="label-tag">{colors['label']}</div>
    <h1 class="page-title">{escape_html(page_title)}</h1>
  </div>

  {content_html}

  <div class="page-footer">
    <div class="footer-logo">一般財団法人 阿部 亮 財団</div>
    <p>©Abe Ryo Foundation</p>
  </div>

</div>
</body>
</html>'''
    
    return html


def build_content(sections, images, template_type):
    """Build the main content HTML from sections and images."""
    html_parts = []
    img_idx = 0
    
    # Hero image (first image if available)
    if images and img_idx < len(images):
        hero = images[img_idx]
        html_parts.append(f'<img class="hero-image" src="{hero["path"]}" alt="活動写真">')
        img_idx += 1
    
    for i, section in enumerate(sections):
        if section.get('type') == 'page_title':
            continue
        
        sec_html = '<div class="section-block">'
        
        if section.get('title'):
            title = section['title']
            # Detect if it's a sub-style heading
            if title.startswith('◎') or title.startswith('【') or title.startswith('■'):
                sec_html += f'<h3 class="section-subheading">{escape_html(title)}</h3>'
            else:
                sec_html += f'<h2 class="section-heading">{escape_html(title)}</h2>'
        
        # Insert images at natural breakpoints
        body_lines = section.get('body', [])
        
        # Split body into paragraphs
        paragraphs = split_into_paragraphs(body_lines)
        
        for j, para in enumerate(paragraphs):
            if para.strip():
                sec_html += f'<p class="section-text">{escape_html(para)}</p>'
            
            # Insert image after every 2nd paragraph
            if (j + 1) % 2 == 0 and img_idx < len(images):
                img_block, img_idx = insert_image_block(images, img_idx, template_type, section)
                sec_html += img_block
        
        # Add remaining image if section has content
        if img_idx < len(images) and (section.get('title') or body_lines):
            # Check if we should add a pair or single
            remaining = len(images) - img_idx
            if remaining >= 2 and i % 3 == 0:
                sec_html += f'''<div class="img-pair">
  <img src="{images[img_idx]["path"]}" alt="活動写真">
  <img src="{images[img_idx+1]["path"]}" alt="活動写真">
</div>'''
                img_idx += 2
            elif remaining >= 1:
                sec_html += f'<div class="img-single"><img src="{images[img_idx]["path"]}" alt="活動写真"></div>'
                img_idx += 1
        
        sec_html += '</div>'
        html_parts.append(sec_html)
    
    # Add any remaining images at the end
    while img_idx < len(images):
        remaining = len(images) - img_idx
        if remaining >= 3:
            html_parts.append(f'''<div class="img-trio">
  <img src="{images[img_idx]["path"]}" alt="活動写真">
  <img src="{images[img_idx+1]["path"]}" alt="活動写真">
  <img src="{images[img_idx+2]["path"]}" alt="活動写真">
</div>''')
            img_idx += 3
        elif remaining >= 2:
            html_parts.append(f'''<div class="img-pair">
  <img src="{images[img_idx]["path"]}" alt="活動写真">
  <img src="{images[img_idx+1]["path"]}" alt="活動写真">
</div>''')
            img_idx += 2
        else:
            html_parts.append(f'<div class="img-single"><img src="{images[img_idx]["path"]}" alt="活動写真"></div>')
            img_idx += 1
    
    return '\n'.join(html_parts)


def insert_image_block(images, img_idx, template_type, section):
    """Insert appropriate image block based on context."""
    if img_idx >= len(images):
        return '', img_idx
    
    img = images[img_idx]
    
    # Hospital template: patient interviews get profile cards
    if template_type == 'hospital' and 'インタビュー' in (section.get('title', '') or ''):
        block = f'''<div class="profile-card">
  <img src="{img["path"]}" alt="患者写真">
  <div class="profile-info">
    <h4>患者インタビュー</h4>
    <p>患者さんの声</p>
  </div>
</div>'''
    else:
        block = f'<div class="img-single"><img src="{img["path"]}" alt="活動写真"></div>'
    
    return block, img_idx + 1


def split_into_paragraphs(lines):
    """Merge lines into natural paragraphs."""
    if not lines:
        return []
    
    paragraphs = []
    current = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current:
                paragraphs.append(' '.join(current))
                current = []
        elif line.endswith('。') or line.endswith('。\n') or len(line) > 80:
            current.append(line)
            paragraphs.append(' '.join(current))
            current = []
        else:
            current.append(line)
    
    if current:
        paragraphs.append(' '.join(current))
    
    return [p for p in paragraphs if p.strip()]


def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ''
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;'))
