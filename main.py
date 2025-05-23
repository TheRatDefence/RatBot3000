import enum
from google import genai
import os
from pydantic import BaseModel
from pydantic import Field
import pickle
import textwrap

class Quiz(BaseModel):                                                # The quiz object/class which is used by gemini to create a structured output
    quiz_prompt: str = Field(description="The prompt used to generate the quiz")
    class Question(BaseModel): # Question object/class used by gemini
        class Answer(BaseModel): # Answer object/class used by gemini
            class Letter(enum.Enum): # Letter enum object/class used by gemini
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

    class FormatedQuestion:                                            # The class used to generate usable questions from the quiz object
        counter = 0
        def __init__(self, pre_question):
            self.wrong_answers = {} # Dict of all wrong answers
            self.right_answer = {} # Dict of all right answers (just 1)
            self.answers = {} # Dict of all answers
            self.question_text = pre_question.question.replace('\n', '') # The question text that is being asked of the user
            self.user_answer = '' # The letter the user inputs as their answer
            self.number = Quiz.FormatedQuestion.counter # The number of the question
            self.explanation = '' # The generated explanation of the question
            
            for i in range(4):                                          # Loops 4 times
                letter = str(pre_question.answers[i].letter.value)      # Gets the letter from the answer object
                answer = str(pre_question.answers[i].answer)            # Gets the answer from the answer object

                self.answers.update({letter: answer})                   # Appends the letter and answer to the answers dict

                if letter != str(pre_question.correct_answer.value):    # Sorts the letter: answer dict entry into the right or wrong answer dict
                    self.wrong_answers.update({letter: answer})
                else:
                    self.right_answer.update({letter: answer})

            Quiz.FormatedQuestion.counter += 1

        def print(self):                                                # Function for printing out each question
            boxed_text("", True)
            boxed_text(" ", False)
            width = os.get_terminal_size().columns
            boxed_text(f"[Q{self.number + 1}] {self.question_text}...", False)
            boxed_text(" ", False)

            for letter, answer in self.answers.items():
                boxed_text(f"{letter} -> {answer}", False)


            boxed_text(" ", False)
            boxed_text("", True)

        def explain(self):
            if self.explanation == '':
                width = os.get_terminal_size().columns

                extention_math_outcomes = """Objective Students:  develop efficient strategies to solve problems using pattern recognition, generalisation, proof and modelling techniques 
                Year 10 Mathematics Extension 1 outcomes A student:
                ME10-1 uses algebraic and graphical concepts in the modelling and solving of problems involving functions and their inverses
                Year 11 Mathematics Extension 1 outcomes A student:  ME12-1 applies techniques involving proof or calculus to model and solve problems 


                Mathematics Extension 0 Stage 6 Syllabus (2017) 18 Objective Students: develop the ability to use concepts and skills and apply complex techniques to the solution of problems and modelling in the areas of trigonometry, functions, calculus, proof, vectors and statistical analysis 

                Year 10 Mathematics Extension 1 outcomes A student: 
                ME10-2 manipulates algebraic expressions and graphical functions to solve problems 
                ME10-3 applies concepts and techniques of inverse trigonometric functions and simplifying expressions involving compound angles in the solution of problems
                ME10-4 applies understanding of the concept of a derivative in the solution of problems, including rates of change, exponential growth and decay and related rates of change 
                ME10-5 uses concepts of permutations and combinations to solve problems involving counting or ordering

                Year 11 Mathematics Extension 1 outcomes A student: ME12-2 applies concepts and techniques involving vectors and projectiles to solve problems
                ME11-3 applies advanced concepts and techniques in simplifying expressions involving compound angles and solving trigonometric equations ME12-4 uses calculus in the solution of applied problems, including differential equations and volumes of solids of revolution  ME12-5 applies appropriate statistical processes to present, analyse and interpret data 


                Objective Students: use technology effectively and apply critical thinking to recognise appropriate times for such use 
                Year 10 Mathematics Extension 1 outcomes A student:
                ME10-6 uses appropriate technology to investigate, organise and interpret information to solve problems in a range of contexts
                Year 11 Mathematics Extension 1 outcomes A student:  ME12-6 chooses and uses appropriate technology to solve problems in a range of contexts

                Mathematics Extension 0 Stage 6 Syllabus (2017) 19 Objective Students:
                develop the ability to interpret, justify and communicate mathematics in a variety of forms 

                Year 10 Mathematics Extension 1 outcomes A student: 
                ME10-7 communicates making comprehensive use of mathematical language, notation, diagrams and graphs
                Year 11 Mathematics Extension 1 outcomes A student:  
                ME11-7 evaluates and justifies conclusions, communicating a position clearly in appropriate mathematical forms"""

                print("\t[I] Generating explanation...")
                with open("api_key.txt", "r") as f:         # Get the API key from the file
                    api_key = f.read().strip()
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(   # Generate the explanation using the gemini API
                    model="gemini-2.0-flash",
                    contents=f"Explain how to solve the following question: {self.question_text} and where the user might have gone wrong with their answer: {self.user_answer}, also ensure that if any sentence goes over {width/2} characters, it is split into multiple lines. "
                              f" Keep the explanation short and simple, and do not use any latex or unicode characters that cannot be printed to a terminal and do not use markdown."
                              f" Ensure the quiz and questions help the user learn and achieve at least one of these outcomes: {extention_math_outcomes} "
                              f" Make sure that the outcome name is also included in the question to help the user identify the outcome they were learning.",
                )

                self.explanation = response.text            # Assigning the response to the explanation variable
                print("\t[I] Explanation: ")

                boxed_text("", True)
                boxed_text(" ", False)
                boxed_text(self.explanation, False)         # Display the explanation
                boxed_text(" ", False)
                boxed_text("", True)

            else:
                print("\t[I] Explanation already generated.")
                print("\t[I] Explanation: ")
                centered_question(self.explanation)

            centered_question("Press enter to continue to the next question...")

        def get_question_answer(self) -> bool:                           # Function for getting the answer from the user
            if self.user_answer == '':
                self.print()                                                              # Display the question

                user_input = multichoice_question("The answer is... (A/B/C/D): ")         # Ask the user for input

                while not user_input in self.answers.keys():                              # Check if the input is valid
                    print("\t[E] Invalid answer. Please try again.")
                    user_input = multichoice_question("The answer is... (A/B/C/D): ")

                self.user_answer = user_input                                             # Assign user input to the user_answer variable
                clear_screen()
                return True
            return False



        def is_correct_answer(self):                                      # Function for checking if the answer is correct
            if self.user_answer in self.right_answer.keys():
                return True
            else:
                return False

    def format(self):                                                     # Function which converts Quiz.Question objects to Quiz.FormatedQuestion objects
        formated_questions = []
        for question in self.pre_questions:
            formated_questions.append(self.FormatedQuestion(question))
        return formated_questions

def create_quiz(number: int, prompt: str):                                # The function which generates the quiz using the gemini API
    try:
        with open("api_key.txt", "r") as f:                     #Attempt to load the API key from the file
            api_key = f.read().strip()
        client = genai.Client(api_key=api_key)
    except:
        print("\t[E] No API key found. Please create a file called api_key.txt with your API key.")
        return False

    print("\t[I] Generating quiz...")

    extention_math_outcomes = """Objective Students:  develop efficient strategies to solve problems using pattern recognition, generalisation, proof and modelling techniques 
    Year 10 Mathematics Extension 1 outcomes A student:
    ME10-1 uses algebraic and graphical concepts in the modelling and solving of problems involving functions and their inverses
    Year 11 Mathematics Extension 1 outcomes A student:  ME12-1 applies techniques involving proof or calculus to model and solve problems 


    Mathematics Extension 0 Stage 6 Syllabus (2017) 18 Objective Students: develop the ability to use concepts and skills and apply complex techniques to the solution of problems and modelling in the areas of trigonometry, functions, calculus, proof, vectors and statistical analysis 

    Year 10 Mathematics Extension 1 outcomes A student: 
    ME10-2 manipulates algebraic expressions and graphical functions to solve problems 
    ME10-3 applies concepts and techniques of inverse trigonometric functions and simplifying expressions involving compound angles in the solution of problems
    ME10-4 applies understanding of the concept of a derivative in the solution of problems, including rates of change, exponential growth and decay and related rates of change 
    ME10-5 uses concepts of permutations and combinations to solve problems involving counting or ordering

    Year 11 Mathematics Extension 1 outcomes A student: ME12-2 applies concepts and techniques involving vectors and projectiles to solve problems
    ME11-3 applies advanced concepts and techniques in simplifying expressions involving compound angles and solving trigonometric equations ME12-4 uses calculus in the solution of applied problems, including differential equations and volumes of solids of revolution  ME12-5 applies appropriate statistical processes to present, analyse and interpret data 


    Objective Students: use technology effectively and apply critical thinking to recognise appropriate times for such use 
    Year 10 Mathematics Extension 1 outcomes A student:
    ME10-6 uses appropriate technology to investigate, organise and interpret information to solve problems in a range of contexts
    Year 11 Mathematics Extension 1 outcomes A student:  ME12-6 chooses and uses appropriate technology to solve problems in a range of contexts

    Mathematics Extension 0 Stage 6 Syllabus (2017) 19 Objective Students:
    develop the ability to interpret, justify and communicate mathematics in a variety of forms 

    Year 10 Mathematics Extension 1 outcomes A student: 
    ME10-7 communicates making comprehensive use of mathematical language, notation, diagrams and graphs
    Year 11 Mathematics Extension 1 outcomes A student:  
    ME11-7 evaluates and justifies conclusions, communicating a position clearly in appropriate mathematical forms"""

    try:                                                          # Attempt to generate the quiz using the gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Generate a math's quiz that follows the course outcomes with {number} questions on the topic of {prompt}. "
                     f"The questions must follow the A B C D structure and be sensible choices. "
                     f"Ensure that there is only 1 correct answer and that it is correct. "
                     f"Do not display the math questions in latex, only unicode characters that can be printed to a terminal"
                     f"Ensure that the quiz and questions help the user learn and achieve at least one of these outcomes: {extention_math_outcomes} "
                     f"Make sure that the outcome name is also included in the question to help the user identify the outcome they were learning.",
            config={
                'response_mime_type': 'application/json',
                'response_schema': Quiz,
            },
        )
        return response.parsed.format()
    except:                                                         # If the gemini API fails to generate the quiz, it's due to the API key being invalid
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
        for text_line in textwrap.wrap(text, width=hwidth - 2, break_on_hyphens=True):
            if text_line != "\n":
                print(" " * qwidth + "|" + text_line.center(hwidth - 2, " ") + "|" + " " * qwidth)
            else:
                print(" " * qwidth + "|" + ("#" * (width - 2)) + "|" + " " * qwidth)
    if line:
        print(" " * qwidth + "-" * hwidth + " " * qwidth)


def display_quiz(questions):                                              # Function which displays the quiz and checks the answers
    correct_answers = 0

    clear_screen()

    for question in questions:                                   # Loop through each question
        if question.get_question_answer():                       # Get the answer from the user
            update_quiz(questions)                               # Update the quiz object in the file
        if question.is_correct_answer():                         # Check if the answer is correct
            correct_answers += 1                                 # Increment the correct answers counter

    clear_screen()

    print("[I]\tChecking answers...")
    centered_question(f"You got {correct_answers} out of {len(questions)} questions correct.")
    if correct_answers != len(questions): # Check if the user got all questions correct
        if centered_question("Would you like to see the questions you got wrong? (y/n): "):
            for question in questions: # Loop through each question again
                if not question.is_correct_answer(): # Check if the answer is incorrect
                    clear_screen()
                    question.print()                                                                                                           # Display the question
                    centered_question(f"Your answer: {question.user_answer} -> {question.answers[question.user_answer]}")                      # Display the user's answer
                    centered_question(f"Correct answer: {list(question.right_answer.keys())[0]} -> {list(question.right_answer.values())[0]}") # Display the correct answer
                    if centered_question("Would you like to see an explanation? (y/n): "):
                        question.explain()                                                                                                     # Use the explain function to generate an explanation of how to solve the question
    print("\t[I] Ending program!")


def main():                                                               # Main function which acts like the main menu
    clear_screen()
    if centered_question("Would you like to create a new quiz? (y/n): "):
        try:
            number = int(multichoice_question("Enter an amount of questions: ").lower()) # Attempt to get the number of questions from the user as int
        except:
            print("\t[E] Invalid input. Please enter a number.")
            return False

        try:
            topic = multichoice_question("Enter a maths topic: ").lower() # Attempt to get the topic from the user as string and convert it to lowercase
        except:
            print("\t[E] Invalid input. Please enter a topic.")
            return False


        quiz = create_quiz(number, topic) # Create the quiz using the create_quiz function
        if not quiz: # Check if the quiz was created successfully
            print("\t[E] Quiz generation failed. Please try again.")
            return False
        with open("quiz.pkl", "wb") as f: #Save the quiz object to file
            pickle.dump(quiz, f)
        print("\t[I] Quiz created and saved to quiz.pkl")

    else:
        try:
            with open("quiz.pkl", "rb") as f: # Attempt to load the quiz from the file
                quiz = pickle.load(f)
                print("\t[I] Quiz loaded from quiz.pkl")
        except:
            print("\t[E] No quiz found. Please create a new quiz.")
            return False

    if centered_question("Start quiz? (y/n): "): # The user is asked if they want to start the quiz
        display_quiz(quiz)
    else:
        return False
    return True

if __name__=="__main__":
    while not main():
        if str(input("\n" * 2 + "Restart program? (y/n): ")).lower() == "y": # Everytime main() returns false, the user is asked if they want to restart the program
            print("Restarting program...")
            main()
        else:
            exit()

    exit()


