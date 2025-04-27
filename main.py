import enum
from google import genai
import os
from pydantic import BaseModel
from pydantic import Field
import pickle

class Quiz(BaseModel):                                                              # The quiz object/class which is used by gemini to create a structured output
    quiz_prompt: str = Field(description="The prompt used to generate the quiz")
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

    class FormatedQuestion:                                           # The class used to generate usable questions from the quiz object
        counter = 0
        def __init__(self, pre_question):
            self.wrong_answers = {}
            self.right_answer = {}
            self.answers = {}
            self.question_text = pre_question.question
            self.user_answer = ''
            self.number = Quiz.FormatedQuestion.counter
            self.explanation = ''
            
            for i in range(4):
                letter = str(pre_question.answers[i].letter.value)
                answer = str(pre_question.answers[i].answer)

                self.answers.update({letter: answer})

                if letter != str(pre_question.correct_answer.value):
                    self.wrong_answers.update({letter: answer})
                else:
                    self.right_answer.update({letter: answer})

            Quiz.FormatedQuestion.counter += 1

        def print(self):                                               # Function for printing out each question
            boxed_text("", True)
            boxed_text(" ", False)
            boxed_text(f"[Q{self.number + 1}] {self.question_text}...", False)
            boxed_text(" ", False)

            for letter, answer in self.answers.items():
                boxed_text(f"{letter} -> {answer}", False)


            boxed_text(" ", False)
            boxed_text("", True)

        def explain(self):
            if self.explanation == '':
                width = os.get_terminal_size().columns


                print("\t[I] Generating explanation...")
                with open("api_key.txt", "r") as f:
                    api_key = f.read().strip()
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Explain how to solve the following question: {self.question_text} and where the user might have gone wrong with their answer: {self.user_answer}, also ensure that if any sentence goes over {width} characters, it is split into multiple lines. "
                              f" Keep the explanation short and simple, and do not use any latex or unicode characters that cannot be printed to a terminal and do not use markdown. The maximum length of text on one line should be {width} characters. ",
                )

                self.explanation = response.text
                print("\t[I] Explanation: ")

                boxed_text("", True)
                boxed_text(" ", False)
                for line in self.explanation.splitlines():
                    boxed_text(line, False)

                boxed_text(" ", False)
                boxed_text("", True)

            else:
                print("\t[I] Explanation already generated.")
                print("\t[I] Explanation: ")
                centered_question(self.explanation)

            centered_question("Press enter to continue to the next question...")

        def get_question_answer(self) -> bool:                          # Function for getting the answer from the user
            if self.user_answer == '':
                self.print()

                user_input = multichoice_question("The answer is... (A/B/C/D): ")

                while not user_input in self.answers.keys():
                    print("\t[E] Invalid answer. Please try again.")
                    user_input = multichoice_question("The answer is... (A/B/C/D): ")

                self.user_answer = user_input
                clear_screen()
                return True
            return False



        def is_correct_answer(self):                                     # Function for checking if the answer is correct
            if self.user_answer in self.right_answer.keys():
                return True
            else:
                return False

    def format(self):                                                    # Function which converts Quiz.Question objects to Quiz.FomatedQuestion objects
        formated_questions = []
        for question in self.pre_questions:
            formated_questions.append(self.FormatedQuestion(question))
        return formated_questions

def create_quiz(number: int, prompt: str):                                           # The function which generates the quiz using the gemini API
    try:
        with open("api_key.txt", "r") as f:
            api_key = f.read().strip()
        client = genai.Client(api_key=api_key)
    except:
        print("\t[E] No API key found. Please create a file called api_key.txt with your API key.")
        return False

    print("\t[I] Generating quiz...")


    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Generate a math's quiz with {number} questions on the topic of {prompt}. "
                     f"The questions must follow the A B C D structure and be sensible choices. "
                     f"Ensure that there is only 1 correct answer and that it is correct. "
                     f"Do not display the math questions in latex, only unicode characters that can be printed to a terminal",
            config={
                'response_mime_type': 'application/json',
                'response_schema': Quiz,
            },
        )
        return response.parsed.format()
    except:
        print("\t[E] Invalid API key. Please try again.")
        return False

def update_quiz(quiz):                                                    # Function which updates the quiz object stored in "quiz.pkl"
    with open("quiz.pkl", "wb") as f:
        pickle.dump(quiz, f)
        print("\t[I] Quiz updated and saved to quiz.pkl")

def centered_question(question) -> bool:                                  # Utility function for centering the question in the terminal
    width = os.get_terminal_size().columns
    spacing = " " * int(((width / 2)) - (len(question) / 2))
    formated_question = spacing + question
    return str(input(formated_question)).lower() == "y"

def multichoice_question(question) -> str:                                # Utility function which asks the user for input while being centered
    width = os.get_terminal_size().columns
    spacing = " " * int(((width / 2)) - (len(question) / 2))
    formated_question = spacing + question
    return str(input(formated_question)).upper()

def clear_screen():                                                       # Utility function for clearing the screen then displaying the header
    debugging = False
    if not debugging:
        os.system("cls" if os.name == "nt" else "clear")
        width = os.get_terminal_size().columns
        welcometext = "|| Maths Quiz Generator ||"


        print("#"*width + "\n" + "#"*width)
        print(welcometext.center(width,"#"))
        print("#" * width + "\n" + "#" * width + "\n" + "-" * width + '\n' *  2)

def boxed_text(text: str, line: bool):                                    # Utility function for printing out the text in a box
    width = os.get_terminal_size().columns
    hwidth = int(width / 2)
    qwidth = int(hwidth / 2)

    if not line:
        print(" " * qwidth + "|" + text.center(hwidth - 2, " ") + "|" + " " * qwidth)
    if line:
        print(" " * qwidth + "-" * hwidth + " " * qwidth)


def display_quiz(questions):                                                    # Function which displays the quiz and checks the answers
    correct_answers = 0

    clear_screen()

    for question in questions:
        if question.get_question_answer():
            update_quiz(questions)
        if question.is_correct_answer():
            correct_answers += 1

    clear_screen()

    print("[I]\tChecking answers...")
    centered_question(f"You got {correct_answers} out of {len(questions)} questions correct.")
    if correct_answers != len(questions):
        if centered_question("Would you like to see the questions you got wrong? (y/n): "):
            for question in questions:
                if not question.is_correct_answer():
                    clear_screen()
                    question.print()
                    centered_question(f"Your answer: {question.user_answer} -> {question.answers[question.user_answer]}")
                    centered_question(f"Correct answer: {list(question.right_answer.keys())[0]} -> {list(question.right_answer.values())[0]}")
                    if centered_question("Would you like to see an explanation? (y/n): "):
                        question.explain()
    print("\t[I] Ending program!")


def main():                                                                # Main function which runs the program
    clear_screen()
    if centered_question("Would you like to create a new quiz? (y/n): "):
        try:
            number = int(multichoice_question("Enter an amount of questions: ").lower())
        except:
            print("\t[E] Invalid input. Please enter a number.")
            return False

        try:
            topic = multichoice_question("Enter a maths topic: ").lower()
        except:
            print("\t[E] Invalid input. Please enter a topic.")
            return False


        quiz = create_quiz(number, topic)
        if not quiz:
            print("\t[E] Quiz generation failed. Please try again.")
            return False
        with open("quiz.pkl", "wb") as f:
            pickle.dump(quiz, f)
        print("\t[I] Quiz created and saved to quiz.pkl")

    else:
        try:
            with open("quiz.pkl", "rb") as f:
                quiz = pickle.load(f)
                print("\t[I] Quiz loaded from quiz.pkl")
        except:
            print("\t[E] No quiz found. Please create a new quiz.")
            return False

    if centered_question("Start quiz? (y/n): "):
        display_quiz(quiz)
    else:
        return False
    return True

if __name__=="__main__":
    while not main():
        if str(input("\n" * 2 + "Restart program? (y/n): ")).lower() == "y":
            print("Restarting program...")
            main()
        else:
            exit()

    exit()
