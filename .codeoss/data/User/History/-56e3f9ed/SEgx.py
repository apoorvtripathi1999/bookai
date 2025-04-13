from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename

import os
import vertexai
import pdfplumber
from google.protobuf import wrappers_pb2
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import texttospeech_v1
from google.cloud import speech

project_id = "bookai-456604"
vertexai.init(project=project_id, location="us-central1")
model = GenerativeModel("gemini-2.0-flash-001")
prompt = """
based on the above text answer the following question: --
"""

app = Flask(__name__)


# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



speech_client = speech.SpeechClient()  # for speech-to-text
tts_client = texttospeech_v1.TextToSpeechClient()  # for text-to-speech

def sample_recognize(content):
  audio=speech.RecognitionAudio(content=content)

  config=speech.RecognitionConfig(
  # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
  # sample_rate_hertz=24000,
  language_code="en-US",
  model="latest_long",
  audio_channel_count=1,
  enable_word_confidence=True,
  enable_word_time_offsets=True,
  )

  operation=speech_client.long_running_recognize(config=config, audio=audio)

  response=operation.result(timeout=90)

  txt = ''
  for result in response.results:
    txt = txt + result.alternatives[0].transcript + '\n'
  print(txt)
  return txt


def sample_synthesize_speech(text=None, ssml=None):
    input = texttospeech_v1.SynthesisInput()
    if ssml:
      input.ssml = ssml
    else:
      input.text = text

    voice = texttospeech_v1.VoiceSelectionParams()
    voice.language_code = "en-UK"
    # voice.ssml_gender = "MALE"

    audio_config = texttospeech_v1.AudioConfig()
    audio_config.audio_encoding = "LINEAR16"

    request = texttospeech_v1.SynthesizeSpeechRequest(
        input=input,
        voice=voice,
        audio_config=audio_config,
    )

    response = tts_client.synthesize_speech(request=request)

    return response.audio_content

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
def upload_file():
    pdf_text = ""
    if 'pdf_file' in request.files:
        pdf_file = request.files['pdf_file']
        if pdf_file.filename.endswith('.pdf'):
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(pdf_path)

            text = ""
            with pdfplumber.open(pdf_path) as doc:
                for page in doc.pages:
                    pdf_text += page.extract_text()

            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(pdf_text)
            print("PDF uploaded:", filename)
            print("PDF text:", pdf_text)
            # return redirect('/')

    if 'audio_data' in request.files:
        file = request.files['audio_data']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            with open(file_path, 'rb') as f:
                data = f.read()

            audio_converted_to_text = sample_recognize(data)
            


            final_prompt = pdf_text + prompt + audio_converted_to_text
            print(pdf_text)
            
            contents = [final_prompt]
            response = model.generate_content(contents)
            text = response.text

            print(text)

            with open(file_path + '.txt', 'w') as f:
                f.write(text)

    return redirect('/')




@app.route('/upload/<filename>')
def get_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path)

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)

