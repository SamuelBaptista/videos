import argparse

from repenseai.genai.agent import Agent
from repenseai.genai.tasks.api import Task

# Set up argument parser
parser = argparse.ArgumentParser(description='Character-based conversation with AI')

parser.add_argument(
    'index', 
    type=int, 
    choices=range(4), 
    help='Index of character (0: Elvis, 1: Einstein, 2: Shakespeare, 3: Mona Lisa)'
)

args = parser.parse_args()

agent = Agent(
    model="gpt-4o",
    model_type="chat",
)

task = Task(
    user="You are {character}, Always asnwer the question playing your role.\n\n{user_input}",
    agent=agent,
    simple_response=True
)

characters = ["Elvis", "Einstein", "Shakespeare", "Mona Lisa"]


def chat_loop():

    i = 0

    while True:
        user_input = input("\nYou: ")
        if user_input in ["exit", "quit"]:
            break
        if i == 0:
            response = task.run({"character": characters[args.index], "user_input": user_input})
        else:
            task.add_user_message(user_input)
            response = task.run()

        print()
        print(response.replace(". ", ".\n"))
        i += 1


if __name__ == "__main__":
    chat_loop()