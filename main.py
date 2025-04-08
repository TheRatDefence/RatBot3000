from google import genai
import os

client = genai.Client(api_key=os.environ["api_key"])

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain how AI works",
)

print(response.text)