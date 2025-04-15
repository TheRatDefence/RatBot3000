import enum
from google import genai
import os
from pydantic import BaseModel
from pydantic import Field

class Quiz(BaseModel):
    class Question(BaseModel):
        class Answer(BaseModel):
            class Letter(enum.Enum):
                A = "A"
                B = "B"
                C = "C"
                D = "D"

            letter: Letter = Field(description="The letter for this answer")
            answer: str = Field(description="The text for this answer")

        question: str = Field(description="The text for this question")
        answers: list[Answer] = Field(description="The answers for this question")
        correct_answer: Answer.Letter = Field(description="The correct answer letter for this question")

    pre_questions: list[Question] = Field(description="The list of questions")

    class FormatedQuestion:
        def __init__(self, pre_question):
            self.wrong_answers = {}
            self.right_answer = {}
            self.answers = {}
            self.question_text = pre_question.question

            for i in range(4):
                letter = str(pre_question.answers[i].letter.value)
                answer = str(pre_question.answers[i].answer)

                self.answers.update({letter: answer})

                if letter != str(pre_question.correct_answer.value):
                    self.wrong_answers.update({letter: answer})
                else:
                    self.right_answer.update({letter: answer})

        def print(self):
            print(f"{self.question_text}...")
            for letter, answer in self.answers.items():
                print(f"\t | {letter}: {answer}")
            print(f"\t | Correct answer: {self.right_answer}")

    def format(self):
        formated_questions = []
        for question in self.pre_questions:
            formated_questions.append(self.FormatedQuestion(question))
        return formated_questions

def get_response():
    client = genai.Client(api_key=os.environ["api_key"])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Create 5 very simple addition questions",
        config={
            'response_mime_type': 'application/json',
            'response_schema': Quiz,
        },
    )
    return response.parsed

questions = get_response().format()
for question in questions:
    question.print()