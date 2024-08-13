from flask import Flask, request, send_from_directory, render_template, abort
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Bật CORS
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 10  # 100 GB

# Đảm bảo thư mục uploads tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('app.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    filename = request.form.get('filename')
    start = int(request.form.get('start'))
    end = int(request.form.get('end'))

    if file and filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(b'\0' * end)  # Tạo file trống với kích thước end

        with open(file_path, 'r+b') as f:
            f.seek(start)
            f.write(file.read())

        return 'File chunk uploaded successfully'
    return 'No file uploaded', 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        abort(404, description="File not found")

if __name__ == '__main__':
    app.run(debug=True)
