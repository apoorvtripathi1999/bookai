from vertexai.preview.generative_models import GenerativeModel
import vertexai

vertexai.init(project="bookai-456604", location="us-central1")

model = GenerativeModel("text-bison")
response = model.generate_content("Hello Gemini!")
print(response.text)