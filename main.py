import enum
from google import genai
import os
from pydantic import BaseModel

question_schema = """

{



}


"""


try:
    print("Creating file")
    file = open("QuestionData.txt", "x")

except:
    print("File already exists")


client = genai.Client(api_key=os.environ["api_key"])

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Create 5 very simple addition questions",
    config={
            'response_mime_type': 'application/json',
            'response_schema': list[question_schema],
    },
)

