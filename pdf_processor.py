import os
import re
from PIL import Image
from pypdf import PdfReader
from pdf2image import convert_from_path
from page_generator import generate_page
from text_corrector import correct_text, preprocess_text

def process_pdf(pdf_path, job_id, template_type, output_folder):
    """Extract text and images from PDF, then generate HTML page."""
    
    output_dir = os.path.join(output_folder, job_id)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    # 1. Extract text
    text_content = extract_text(pdf_path)
    
    # 2. Extract images from PDF pages
    extracted_images = extract_images(pdf_path, images_dir, template_type)
    
    # 3. Parse text into structured sections
    sections = parse_text_to_sections(text_content, template_type)

    # 4. AI校正：文字化け・誤字脱字・空白を修正
    sections = correct_text(sections, template_type)
    
    # 5. Generate HTML page
    html_content = generate_page(sections, extracted_images, template_type, job_id)
    
    # Save HTML
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return {
        'job_id': job_id,
        'template_type': template_type,
        'image_count': len(extracted_images),
        'sections': [s['title'] for s in sections if s.get('title')],
    }

def extract_text(pdf_path):
    """Extract all text from PDF and preprocess (join broken lines, fix spaces)."""
    reader = PdfReader(pdf_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            # 行末改行結合・空白修正をページ単位で適用
            full_text.append(preprocess_text(text))
    return '\n\n'.join(full_text)

def extract_images(pdf_path, images_dir, template_type):
    """Extract images by rendering PDF pages and smart-cropping."""
    # Render all PDF pages at high DPI
    pages = convert_from_path(pdf_path, dpi=150, fmt='jpeg')
    
    extracted = []
    
    # Template-based image specs (role: size hints)
    specs = get_image_specs(template_type)
    
    # For each page render, smart-crop into useful images
    for i, page_img in enumerate(pages):
        # Convert to RGB if needed
        if page_img.mode != 'RGB':
            page_img = page_img.convert('RGB')
        
        # Detect if this is a photo-heavy page or text-heavy
        photos = detect_and_crop_photos(page_img, i)
        
        for j, (crop_img, confidence) in enumerate(photos):
            if confidence < 0.3:
                continue
            
            # Apply optimal cropping based on specs
            spec_idx = len(extracted) % len(specs)
            final_img = smart_crop(crop_img, specs[spec_idx]['width'], specs[spec_idx]['height'])
            
            fname = f'img_{i:02d}_{j:02d}.jpg'
            fpath = os.path.join(images_dir, fname)
            final_img.save(fpath, 'JPEG', quality=85)
            extracted.append({
                'filename': fname,
                'path': f'images/{fname}',
                'role': specs[spec_idx]['role'],
                'width': specs[spec_idx]['width'],
                'height': specs[spec_idx]['height'],
            })
        
        # If no photos detected on page, save the whole page as a photo (skip mostly-text pages)
        if not photos and len(pages) <= 10:
            # Check if page has significant non-white area (image content)
            if has_visual_content(page_img):
                spec_idx = len(extracted) % len(specs)
                final_img = smart_crop(page_img, specs[spec_idx]['width'], specs[spec_idx]['height'])
                fname = f'img_{i:02d}_full.jpg'
                fpath = os.path.join(images_dir, fname)
                final_img.save(fpath, 'JPEG', quality=85)
                extracted.append({
                    'filename': fname,
                    'path': f'images/{fname}',
                    'role': specs[spec_idx]['role'],
                    'width': specs[spec_idx]['width'],
                    'height': specs[spec_idx]['height'],
                })
    
    return extracted

def has_visual_content(img):
    """Check if image has substantial visual content (not mostly white/blank)."""
    import statistics
    thumb = img.resize((100, 100))
    pixels = list(thumb.getdata())
    # Calculate variance - high variance = visual content
    r_vals = [p[0] for p in pixels]
    variance = statistics.variance(r_vals)
    # Also check if not too bright (mostly white)
    avg = sum(r_vals) / len(r_vals)
    return variance > 500 and avg < 240

def detect_and_crop_photos(page_img, page_idx):
    """Detect photo regions in a page image using simple heuristics."""
    width, height = page_img.size
    results = []
    
    # Grid-based detection: scan for regions with high color variance
    grid_rows = 4
    grid_cols = 2
    cell_w = width // grid_cols
    cell_h = height // grid_rows
    
    for row in range(grid_rows):
        for col in range(grid_cols):
            x1 = col * cell_w
            y1 = row * cell_h
            x2 = min(x1 + cell_w, width)
            y2 = min(y1 + cell_h, height)
            
            region = page_img.crop((x1, y1, x2, y2))
            confidence = compute_photo_confidence(region)
            
            if confidence > 0.4:
                # Expand slightly
                pad = 10
                x1p = max(0, x1 - pad)
                y1p = max(0, y1 - pad)
                x2p = min(width, x2 + pad)
                y2p = min(height, y2 + pad)
                cropped = page_img.crop((x1p, y1p, x2p, y2p))
                results.append((cropped, confidence))
    
    return results

def compute_photo_confidence(region):
    """Compute likelihood that a region contains a photo (not just text)."""
    import statistics
    thumb = region.resize((50, 50))
    pixels = list(thumb.getdata())
    
    r_vals = [p[0] for p in pixels]
    g_vals = [p[1] for p in pixels]
    b_vals = [p[2] for p in pixels]
    
    # High variance across channels = likely photo
    r_var = statistics.variance(r_vals) if len(r_vals) > 1 else 0
    g_var = statistics.variance(g_vals) if len(g_vals) > 1 else 0
    b_var = statistics.variance(b_vals) if len(b_vals) > 1 else 0
    
    avg_var = (r_var + g_var + b_var) / 3
    avg_brightness = sum(r_vals) / len(r_vals)
    
    # Normalize: photos have high variance and aren't all-white
    confidence = min(1.0, avg_var / 3000)
    if avg_brightness > 245:  # Nearly white = likely blank
        confidence *= 0.1
    
    # Check color diversity (photos have multiple colors)
    unique_pixels = len(set(zip(r_vals[::5], g_vals[::5], b_vals[::5])))
    if unique_pixels < 20:
        confidence *= 0.3
    
    return confidence

def smart_crop(img, target_w, target_h):
    """Crop image to target aspect ratio using center-focused cropping."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h
    
    if src_ratio > target_ratio:
        # Source is wider - crop sides
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    elif src_ratio < target_ratio:
        # Source is taller - crop top/bottom (slightly favor top for portraits)
        new_h = int(src_w / target_ratio)
        top = int((src_h - new_h) * 0.35)  # 35% from top = face-friendly
        img = img.crop((0, top, src_w, top + new_h))
    
    # Resize to target
    img = img.resize((target_w, target_h), Image.LANCZOS)
    return img

def get_image_specs(template_type):
    """Return image size/role specs based on template type."""
    if template_type == 'hospital':
        return [
            {'role': 'hero', 'width': 800, 'height': 500},
            {'role': 'activity', 'width': 600, 'height': 400},
            {'role': 'activity', 'width': 600, 'height': 400},
            {'role': 'patient', 'width': 400, 'height': 300},
            {'role': 'patient', 'width': 400, 'height': 300},
            {'role': 'activity', 'width': 600, 'height': 400},
        ]
    elif template_type == 'school':
        return [
            {'role': 'hero', 'width': 800, 'height': 500},
            {'role': 'school', 'width': 500, 'height': 350},
            {'role': 'school', 'width': 500, 'height': 350},
            {'role': 'children', 'width': 500, 'height': 350},
            {'role': 'children', 'width': 500, 'height': 350},
            {'role': 'activity', 'width': 600, 'height': 400},
        ]
    elif template_type == 'japanese':
        return [
            {'role': 'hero', 'width': 800, 'height': 500},
            {'role': 'classroom', 'width': 600, 'height': 400},
            {'role': 'students', 'width': 500, 'height': 350},
            {'role': 'activity', 'width': 600, 'height': 400},
        ]
    else:  # future
        return [
            {'role': 'hero', 'width': 800, 'height': 500},
            {'role': 'activity', 'width': 600, 'height': 400},
            {'role': 'activity', 'width': 600, 'height': 400},
            {'role': 'detail', 'width': 500, 'height': 350},
        ]

def parse_text_to_sections(text, template_type):
    """Parse extracted text into structured sections."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if not lines:
        return [{'title': 'レポート', 'body': [], 'type': 'text'}]
    
    sections = []
    current_section = {'title': '', 'body': [], 'type': 'text'}
    title_found = False

    for line in lines:
        if len(line) < 2:
            continue

        if not title_found and len(line) > 3:
            title_found = True
            sections.append({'title': line, 'body': [], 'type': 'page_title'})
            current_section = {'title': '', 'body': [], 'type': 'text'}
            continue

        if is_section_header(line):
            if current_section['body'] or current_section['title']:
                sections.append(current_section)
            current_section = {'title': line, 'body': [], 'type': 'section'}
        else:
            current_section['body'].append(line)

    if current_section['body'] or current_section['title']:
        sections.append(current_section)

    # If only a page_title was found, put all body into one section
    content_sections = [s for s in sections if s['type'] != 'page_title']
    if not content_sections:
        body = [l for s in sections for l in s.get('body', [])]
        sections.append({'title': '', 'body': body, 'type': 'text'})

    return sections if sections else [{'title': 'レポート', 'body': lines, 'type': 'text'}]

def is_section_header(line):
    """Determine if a line is a section header."""
    if len(line) < 3 or len(line) > 80:
        return False
    
    # Japanese section markers
    header_patterns = [
        r'^◎', r'^【', r'^■', r'^▲', r'^●', r'^★',
        r'報告$', r'トピック$', r'インタビュー$', r'活動$',
        r'^第\d+', r'^\d+\.',
        # English headers (for test PDFs and bilingual content)
        r'^[A-Z][a-z]+ [A-Z]',  # Title Case phrases
        r'Report$', r'Interview$', r'Activity$',
    ]
    for pattern in header_patterns:
        if re.search(pattern, line):
            return True
    
    # Short standalone lines that look like headings (under 40 chars, no trailing punctuation)
    stripped = line.rstrip('。、，,.')
    if len(stripped) < 40 and not line.endswith('。') and not line.endswith(','):
        # Check if it's significantly shorter than average body text
        # and doesn't look like a sentence fragment
        words = line.split()
        if 2 <= len(words) <= 8 and line[0].isupper():
            return True
    
    return False
