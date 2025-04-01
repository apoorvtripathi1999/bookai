om datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from google.cloud import texttospeech_v1
from google.cloud import aiplatform

# Initialize Text-to-Speech client
tts_client = texttospeech_v1.TextToSpeechClient()

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def transcribe_audio_vertexai(content):
    """Transcribe audio using Google Vertex AI"""
    endpoint = "YOUR_VERTEX_AI_AUDIO_ENDPOINT"
    
    prediction_client = aiplatform.gapic.PredictionServiceClient()
    
    instance = {"content": content}
    instances = [instance]
    
    parameters = {}
    
    response = prediction_client.predict(
        endpoint=endpoint,
        instances=instances,
        parameters=parameters,
    )
    
    transcript = response.predictions[0].get("transcript"fr, "")
    return transcript

def analyze_sentiment_vertexai(text):
    """Perform sentiment analysis using Google Vertex AI"""
    endpoint = "YOUR_VERTEX_AI_TEXT_ANALYSIS_ENDPOINT"
    
    prediction_client = aiplatform.gapic.PredictionServiceClient()
    
    instance = {"text": text}
    instances = [instance]
    
    parameters = {}
    
    response = prediction_client.predict(
        endpoint=endpoint,
        instances=instances,
        parameters=parameters,
    )
    
    sentiment_score = response.predictions[0].get("sentiment_score", 0)
    sentiment_magnitude = response.predictions[0].get("sentiment_magnitude", 0)
    return sentiment_score, sentiment_magnitude

def sample_synthesize_speech(text=None):
    """Convert text to speech using Google Cloud TTS"""
    input_text = texttospeech_v1.SynthesisInput(text=text)
    voice = texttospeech_v1.VoiceSelectionParams(language_code="en-UK")
    audio_config = texttospeech_v1.AudioConfig(audio_encoding="LINEAR16")
    
    response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    return response.audio_content

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
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
    
    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    text = transcribe_audio_vertexai(data)  # Using Vertex AI
    sentiment_score, sentiment_magnitude = analyze_sentiment_vertexai(text)  # Using Vertex AI
    
    sentiment_score = round(sentiment_score, 2)
    sentiment = "Positive" if sentiment_score > 0.75 else "Negative" if sentiment_score < -0.75 else "Neutral"
    
    sentiment_text = f"\nSentiment: {sentiment}\nSentiment Magnitude: {sentiment_magnitude}"
    
    with open(file_path + '.txt', 'w') as f:
        f.write(text)
        f.write(sentiment_text)
    
    return redirect('/')

@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    filename = 'tts' + datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    wav = sample_synthesize_speech(text)
    with open(file_path, 'wb') as f:
        f.write(wav)
    
    sentiment_score, sentiment_magnitude = analyze_sentiment_vertexai(text)  # Using Vertex AI
    sentiment_score = round(sentiment_score, 2)
    sentiment = "Positive" if sentiment_score > 0.75 else "Negative" if sentiment_score < -0.75 else "Neutral"
    
    sentiment_text = f"\nSentiment: {sentiment}\nSentiment Magnitude: {sentiment_magnitude}"
    
    with open(file_path + '.txt', 'w') as f:
        f.write(text)
        f.write(sentiment_text)
    
    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
