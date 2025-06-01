from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESIZED_FOLDER'] = 'resized'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESIZED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    return f"{name}_{timestamp}{ext}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Get dimensions from form
        try:
            width = int(request.form.get('width', 0))
            height = int(request.form.get('height', 0))
            maintain_ratio = 'maintain_ratio' in request.form
        except ValueError:
            return "Invalid dimensions provided", 400

        if width <= 0 and height <= 0:
            return "Please provide valid dimensions", 400

        # Save original file
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(original_path)

        # Process image
        try:
            img = Image.open(original_path)

            # Calculate new dimensions maintaining aspect ratio if requested
            if maintain_ratio:
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height

                if width > 0 and height <= 0:
                    height = int(width / aspect_ratio)
                elif height > 0 and width <= 0:
                    width = int(height * aspect_ratio)
                else:
                    # Both dimensions provided - choose the one that fits better
                    new_width = int(height * aspect_ratio)
                    new_height = int(width / aspect_ratio)

                    if new_width >= width:
                        height = new_height
                    else:
                        width = new_width

            # Resize image
            resized_img = img.resize((width, height), Image.LANCZOS)

            # Save resized image
            resized_filename = f"resized_{unique_filename}"
            resized_path = os.path.join(app.config['RESIZED_FOLDER'], resized_filename)
            resized_img.save(resized_path)

            return render_template('result.html', 
                                original_filename=unique_filename,
                                resized_filename=resized_filename,
                                original_width=img.size[0],
                                original_height=img.size[1],
                                new_width=width,
                                new_height=height)

        except Exception as e:
            return f"Error processing image: {str(e)}", 500

    return "Invalid file type", 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/resized/<filename>')
def resized_file(filename):
    return send_from_directory(app.config['RESIZED_FOLDER'], filename)

if __name__ == '__main__':
    # In production, this block is typically not used;
    # Gunicorn will pick up `app` directly. But if you run `python app.py`,
    # it will bind to 0.0.0.0 and disable debug.
    app.run(host='0.0.0.0', debug=False)
