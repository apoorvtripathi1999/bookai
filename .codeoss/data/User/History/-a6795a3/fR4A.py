
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.cloud.language_v2 import LanguageServiceClient
from google.cloud.language_v2.types import Document, AnalyzeSentimentRequest

sr_client = SpeechClient(client_options={"api_endpoint": "us-central1-speech.googleapis.com"})
language_client = LanguageServiceClient()
app_id = "project-2-convoai"

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sample_recognize(content):
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
        features=cloud_speech.RecognitionFeatures(
            enable_word_confidence=True,
            enable_word_time_offsets=True,
        ),
    )

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", app_id)
    recognizer = f"projects/{project_id}/locations/us-central1/recognizers/_"
    
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer,
        config=config,
        files=[cloud_speech.BatchRecognizeFileMetadata(content=content)],
        recognition_output_config=cloud_speech.RecognitionOutputConfig(
            inline_response_config=cloud_speech.InlineOutputConfig(),
        ),
    )

    operation = sr_client.batch_recognize(request=request)
    response = operation.result(timeout=90)

    txt = ""
    for result in response.results:
        for entry in result.results:
            if entry.alternatives:
                txt += entry.alternatives[0].transcript + "\n"
    return txt

def analyze_sentiment(text):
    document = Document(
        content=text,
        type_=Document.Type.PLAIN_TEXT,
        language_code="en-US",
    )
    request = AnalyzeSentimentRequest(document=document)
    response = language_client.analyze_sentiment(request=request)
    sentiment = response.document_sentiment
    return sentiment.score, sentiment.magnitude

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    files = get_files()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        with open(file_path, 'rb') as f:
            data = f.read()

        text = sample_recognize(data)
        sentiment_score, sentiment_magnitude = analyze_sentiment(text)
        sentiment_score = round(sentiment_score, 2)

        if sentiment_score > 0.75:
            sentiment = "Positive"
        elif sentiment_score < -0.75:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        sentiment_text = f"\nSentiment: {sentiment}\nMagnitude: {sentiment_magnitude:.2f}"

        with open(file_path + '.txt', 'w') as f:
            f.write(text)
            f.write(sentiment_text)

    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/script.js')
def serve_js():
    return send_file('script.js')

if __name__ == '__main__':
    app.run(debug=True)