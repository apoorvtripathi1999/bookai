from vertexai.preview.generative_models import GenerativeModel
import vertexai

vertexai.init(project="your-project-id", location="us-central1")

model = GenerativeModel("gemini-pro")
response = model.generate_content("Hello Gemini!")
print(response.text)