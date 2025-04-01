from datetime import datetime


from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename


import os
import vertexai

# from google.cloud import speech
from google.protobuf import wrappers_pb2
# from google.cloud import texttospeech_v1
# from google.cloud import language
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
audio_file_uri = "gs://convo-ai-2025-feb/test.wav"

# tts_client = texttospeech_v1.TextToSpeechClient()
# sr_client=speech.SpeechClient()


app = Flask(__name__)


# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)




# def sample_recognize(content):
#   audio=speech.RecognitionAudio(content=content)


#   config=speech.RecognitionConfig(
#   # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
#   # sample_rate_hertz=24000,
#   language_code="en-US",
#   model="latest_long",
#   audio_channel_count=1,
#   enable_word_confidence=True,
#   enable_word_time_offsets=True,
#   )


#   operation=sr_client.long_running_recognize(config=config, audio=audio)


#   response=operation.result(timeout=90)


#   txt = ''
#   for result in response.results:
#     txt = txt + result.alternatives[0].transcript + '\n'


#   return txt




# def analyze_sentiment(text):
#     client = language.LanguageServiceClient()
   
#     document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)
#     sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment


#     return sentiment.score, sentiment.magnitude




# def sample_synthesize_speech(text=None, ssml=None):
#     input = texttospeech_v1.SynthesisInput()
#     if ssml:
#       input.ssml = ssml
#     else:
#       input.text = text


#     voice = texttospeech_v1.VoiceSelectionParams()
#     voice.language_code = "en-UK"
#     # voice.ssml_gender = "MALE"


#     audio_config = texttospeech_v1.AudioConfig()
#     audio_config.audio_encoding = "LINEAR16"


#     request = texttospeech_v1.SynthesizeSpeechRequest(
#         input=input,
#         voice=voice,
#         audio_config=audio_config,
#     )


#     response = tts_client.synthesize_speech(request=request)


#     return response.audio_content






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
        # filename = secure_filename(file.filename)
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

        text = sample_recognize(data)
       


        # print(text)


        # sentiment_score, sentiment_magnitude = analyze_sentiment(text)
       
        # sentiment_score = round(sentiment_score, 2)
        # if sentiment_score > 0.75:
        #     sentiment = "Positive"
        # if sentiment_score < - 0.75:
        #     sentiment = "Negative"
        # else:
        #     sentiment = "Neutral"




        # sentiment_text = f"\nSentiment: {sentiment}\nSentiment Magnitude: {sentiment_magnitude}"




        with open(filename + '.txt', 'w') as f:
          f.write(text)
          f.close()


    return redirect('/') #success


@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)


   
# @app.route('/upload_text', methods=['POST'])
# def upload_text():
#     text = request.form['text']
#     print(text)


#     filename = 'tts'+datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)


#     wav = sample_synthesize_speech(text)
   
#     # save audio
#     f = open(file_path,'wb')
#     f.write(wav)
#     f.close()


    # sentiment_score, sentiment_magnitude = analyze_sentiment(text)


    # sentiment_score = round(sentiment_score, 2)
    # if sentiment_score > 0.75:
    #     sentiment = "Positive"
    # if sentiment_score < - 0.75:
    #     sentiment = "Negative"
    # else:
    #     sentiment = "Neutral"


    # sentiment_text = f"\nSentiment: {sentiment}\nSentiment Magnitude: {sentiment_magnitude}"
   
    # #save text
    # with open(file_path + '.txt', 'w') as f:
    #    f.write(text)
    #    f.write(sentiment_text)
    #    f.close()


    # return redirect('/') #success


@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)

