from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename

import os
import vertexai

from google.protobuf import wrappers_pb2
from vertexai.generative_models import GenerativeModel, Part

project_id = "project-2-convoai"
vertexai.init(project=project_id, location="us-central1")
model = GenerativeModel("gemini-1.5-flash-001")
prompt = """
Provide the exact transcript of the audio along with the sentiment analysis:
Format should be like this: 
Text: -- the transcript of the audio--
Sentiment analysis: --Sentiment of the text either positive, negative or neutral--
"""

app = Flask(__name__)


# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
            print(filename)
    files.sort(reverse=True)
    return files


@app.route('/')
def index():
    files = get_files()
    return render_template('index.html', files=files)


@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
       
        filename = file_path
        f = open(file_path,'rb')
        data = f.read()
        f.close()

        print(file_path)

        audio_file = Part.from_data(data, mime_type="audio/waw")
        contents = [audio_file,prompt]
        response = model.generate_content(contents)

        text = response.text
       

        print(text)

        with open(filename + '.txt', 'w') as f:
          f.write(text)
          f.close()


    return redirect('/') #success


@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)


@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)

