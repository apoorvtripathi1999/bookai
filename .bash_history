gcloud auth list
gcloud config list project
gcloud config set project lab1-449822
gcloud services enable translate.googleapis.com
export PROJECT_ID=$(gcloud config get-value core/project)
echo "PROJECT_ID: $PROJECT_ID"
cd ~
virtualenv venv-translate
source venv-translate/bin/activate
ls
gcutil cp feb2024-convoai/*
gsutil cp feb2024-convoai/*
gsutil cp gs://feb2024-convoai/*
gsutil cp gs://feb2024-convoai/* .
ls
python main.py
ls
gsutil rm -r gs://feb2024-convoai/
gcutil cp -r gs://convo-ai-2025-feb/* .
gsutil cp -r gs://convo-ai-2025-feb/* .
ls
python main.py
pip install --upgrade google-cloud-speech
python main.py
python3 -m pip install google-cloud-texttospeech
python main.py
stop
exit
python main.py
python main.py
git init 
git remote add origin https://github.com/apoorvtripathi1999/convo-ai.git
