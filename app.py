import os
import json
import uuid
import shutil
import zipfile
import re
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pdf_processor import process_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

TEMPLATE_TYPES = {
    'hospital': '病院ページ（毎年100人の子どもの命を救うプロジェクト）',
    'school': '学校ページ（世界に学校を建てようプロジェクト）',
    'japanese': '日本語ページ（ミャンマーで日本語を教えようプロジェクト）',
    'future': '未来ページ（子どもの未来を広げる活動）',
}

@app.route('/')
def index():
    return render_template('index.html', templates=TEMPLATE_TYPES)

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return jsonify({'error': 'PDFファイルが選択されていません'}), 400
    
    pdf_file = request.files['pdf']
    template_type = request.form.get('template_type', 'hospital')
    
    if pdf_file.filename == '':
        return jsonify({'error': 'ファイル名が空です'}), 400
    
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'PDFファイルのみ対応しています'}), 400

    job_id = str(uuid.uuid4())[:8]
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{job_id}.pdf')
    pdf_file.save(upload_path)

    try:
        result = process_pdf(upload_path, job_id, template_type, app.config['OUTPUT_FOLDER'])
        return jsonify({'success': True, 'job_id': job_id, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)

@app.route('/preview/<job_id>')
def preview(job_id):
    # Sanitize job_id
    job_id = re.sub(r'[^a-zA-Z0-9_-]', '', job_id)
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    html_path = os.path.join(output_dir, 'index.html')
    if not os.path.exists(html_path):
        return 'ページが見つかりません', 404
    return send_from_directory(output_dir, 'index.html')

@app.route('/output/<job_id>/<path:filename>')
def output_file(job_id, filename):
    job_id = re.sub(r'[^a-zA-Z0-9_-]', '', job_id)
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    return send_from_directory(output_dir, filename)

@app.route('/download/<job_id>')
def download(job_id):
    job_id = re.sub(r'[^a-zA-Z0-9_-]', '', job_id)
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    if not os.path.exists(output_dir):
        return 'ファイルが見つかりません', 404
    
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{job_id}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    return send_file(zip_path, as_attachment=True, download_name=f'aberyo_blog_{job_id}.zip')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
