from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from google.cloud import aiplatform

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def transcribe_and_analyze_sentiment(audio_content):
    """
    Uses Vertex AI to transcribe the audio and perform sentiment analysis.
    """
    endpoint = "projects/YOUR_PROJECT_ID/locations/YOUR_REGION/publishers/google/models/audio-to-text" 
    response = aiplatform.gapic.PredictionServiceClient().predict(
        endpoint=endpoint,
        instances=[{"content": audio_content}],
    )
    text = response.predictions[0]["transcript"] if response.predictions else ""
    
    sentiment_endpoint = "projects/YOUR_PROJECT_ID/locations/YOUR_REGION/publishers/google/models/text-sentiment" 
    sentiment_response = aiplatform.gapic.PredictionServiceClient().predict(
        endpoint=sentiment_endpoint,
        instances=[{"content": text}],
    )
    sentiment_score = sentiment_response.predictions[0]["score"] if sentiment_response.predictions else 0
    
    sentiment = "Positive" if sentiment_score > 0.75 else "Negative" if sentiment_score < -0.75 else "Neutral"
    
    return text, sentiment, sentiment_score

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    return sorted(
        [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)], 
        reverse=True
    )

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
    
    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        text, sentiment, sentiment_score = transcribe_and_analyze_sentiment(audio_data)
        
        sentiment_text = f"\nSentiment: {sentiment}\nSentiment Score: {sentiment_score}"
        
        with open(file_path + '.txt', 'w') as f:
            f.write(text)
            f.write(sentiment_text)
        
    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
