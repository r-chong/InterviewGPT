#!/bin/env python
# imports

import atexit
import click
import os
import requests
import sys
import yaml
import re
import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

from pathlib import Path
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown

WORKDIR = Path(__file__).parent
CONFIG_FILE = Path(WORKDIR, "config.yaml")
HISTORY_FILE = Path(WORKDIR, ".history")
BASE_ENDPOINT = "https://api.openai.com/v1"
ENV_VAR = "OPENAI_API_KEY"
HISTORY_FILE = Path(WORKDIR, "conversation_history.txt")

# for calculation of how much this costs for api calls
# we are not using gpt 4
PRICING_RATE = {
    "gpt-3.5-turbo": {"prompt": 0.002, "completion" :0.002},
    # "gpt-4": {"prompt": 0.03, "completion": 0.06},
    # "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
}

# Get a Firestore client
db = firestore.client()

# Function to verify interview key and mark interview as done
def verify_interview_key(candidate_id, interview_key):
    # Reference the candidate document
    candidate_ref = db.collection('candidates').document(candidate_id)

    # Get the candidate document
    candidate_doc = candidate_ref.get()

    # Verify interview key
    if candidate_doc.exists:
        data = candidate_doc.to_dict()
        saved_key = data.get('interviewKey')

        if saved_key == interview_key:
            # Interview key is valid, mark interview as done
            candidate_ref.update({'interviewDone': True})
            print("Your interview is ready to begin. When you are ready, please prompt the interviewer to start the interview.")
        else:
            print("Invalid interview key.")
    else:
        print("Candidate not found.")

# messages history list
# mandatory to pass it @ each API call in order to have conversation
messages = []
# Initialize the token counters
prompt_tokens = 0
completion_tokens = 0
# Initialize the console
console = Console()

# FILE UPLOAD
def should_prompt_for_file(question):
    file_upload_keywords = ["Critical thinking question","Write a function","Programming question:","Implement a function"]
    for keyword in file_upload_keywords:
        if re.search(r'\b' + keyword.lower() + r'\b', question.lower()):
            return True
    return False

def process_solution(file_path):
    # Check if the file exists
    
    # Read the contents of the file
    with open(file_path, 'r') as file:
        solution_code = file.read()

    console.print("received. processing...")

    # Get the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Format the file contents
    formatted_solution = f"\n\n========== Solution Code ==========\n\n{solution_code}\n\n========== End of Solution Code ==========\n"
    
    # Append the formatted solution to conversation_history.txt
    with open('conversation_history.txt', 'a') as history_file:
        history_file.write(formatted_solution)
    
    return solution_code

def load_config(config_file: str) -> dict:
    """
    Read a YAML config file and returns it's content as a dictionary
    """
    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    return config


def add_markdown_system_message() -> None:
    """
    Try to force ChatGPT to always respond with well formatted code blocks if markdown is enabled.
    """
    instruction = "Always use code blocks with the appropriate language tags"
    messages.append({"role": "system", "content": instruction})

# for development to see how much api costs
def calculate_expense(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_pricing: float,
    completion_pricing: float,
) -> float:
    """
    Calculate the expense, given the number of tokens and the pricing rates
    """
    expense = ((prompt_tokens / 1000) * prompt_pricing) + (
        (completion_tokens / 1000) * completion_pricing
    )
    return round(expense, 6)

# will be built upon
def submit_progress():
    # Code to submit progress to the recruiter
    print("Your progress has been submitted to the recruiter.")


def display_expense(model: str) -> None:
    """
    Given the model used, display total tokens used and estimated expense
    """
    total_expense = calculate_expense(
        prompt_tokens,
        completion_tokens,
        PRICING_RATE[model]["prompt"],
        PRICING_RATE[model]["completion"],
    )
    console.print(
        f"\nTotal tokens used: [green bold]{prompt_tokens + completion_tokens}"
    )
    console.print(f"Estimated expense: [green bold]${total_expense}")


def start_prompt(session: PromptSession, config: dict) -> None:
    """
    Ask the user for input, build the request and perform it
    """

    # TODO: Refactor to avoid a global variables
    global prompt_tokens, completion_tokens

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api-key']}",
    }

    # this is the little icon that shows where the user can type
    message = session.prompt(HTML(f"<b>> </b>"))

    # Exit if user types /q
    if message.lower() == "/q":
        raise EOFError
    if message.lower() == "":
        raise KeyboardInterrupt

    # Add markdown system message if markdown is enabled
    messages.append({"role": "user", "content": message})

    # Save messages to file
    with open(HISTORY_FILE, "a") as file:
        file.write(f"user: {message}\n")

    # Base body parameters
    body = {
        "model": config["model"],
        "temperature": config["temperature"],
        "messages": messages,
    }
    # Optional parameter
    if "max_tokens" in config:
        body["max_tokens"] = config["max_tokens"]

    # main prompt call
    try:
        r = requests.post(
            f"{BASE_ENDPOINT}/chat/completions", headers=headers, json=body
        )
    except requests.ConnectionError:
        console.print("Connection error, try again...", style="red bold")
        messages.pop()
        raise KeyboardInterrupt
    except requests.Timeout:
        console.print("Connection timed out, try again...", style="red bold")
        messages.pop()
        raise KeyboardInterrupt

    # if success, put data into json
    if r.status_code == 200:
        response = r.json()

        message_response = response["choices"][0]["message"]
        usage_response = response["usage"]

        console.line()
        if config["markdown"]:
            console.print(Markdown(message_response["content"].strip()))
        else:
            console.print(message_response["content"].strip())
        console.line()

        # Save AI response to file
        with open(HISTORY_FILE, "a") as file:
            file.write(f"AI: {message_response['content'].strip()}\n")

        # Example usage
        question = message_response["content"].strip()
        solution_code = None
        if should_prompt_for_file(question):
            valid_file = False
            console.print("Please write your response in a separate file and attach the path here.")
            
            while not valid_file:
                # Prompt the user for the file path
                file_path = input("Enter the file path of your solution: ")

                if not os.path.isfile(file_path):
                    print("Invalid file path. Please try again.")
                    continue
                
                valid_file = True
                # Call the function to process the solution

                # Include the solution_code in the body if it is not None
                # messages.append(process_solution(file_path))
        else:
            print("You can answer in the chat.")

        # Update message history and token counters
        messages.append(message_response)
        prompt_tokens += usage_response["prompt_tokens"]
        completion_tokens += usage_response["completion_tokens"]

    # ... (rest of the code remains the same)



@click.command()
@click.option(
    "-c", "--context", "context", type=click.File("r"), help="Path to a context file",
    multiple=True
)
@click.option("-k", "--key", "api_key", help="Set the API Key")
@click.option("-m", "--model", "model", help="Set the model")
def main(context, api_key, model) -> None:
    history = FileHistory(HISTORY_FILE)
    session = PromptSession(history=history)

    try:
        config = load_config(CONFIG_FILE)
    except FileNotFoundError:
        console.print("Configuration file not found", style="red bold")
        sys.exit(1)

    # Order of precedence for API Key configuration:
    # Command line option > Environment variable > Configuration file

    # If the environment variable is set overwrite the configuration
    if os.environ.get(ENV_VAR):
        config["api-key"] = os.environ[ENV_VAR].strip()
    # If the --key command line argument is used overwrite the configuration
    if api_key:
        config["api-key"] = api_key.strip()
    # If the --model command line argument is used overwrite the configuration
    if model:
        config["model"] = model.strip()

    # Run the display expense function when exiting the script
    atexit.register(submit_progress)
    atexit.register(display_expense, model=config["model"])

    # Display the welcome message
    console.print("InterviewGPT | Revolutionizing online assessments in technology.", style="green bold italic")
    console.print("\nYour activity within this interface will be tracked for evaluation and analysis purposes."
                  + "\nBy using this program, you agree to the collection and usage of your data for these purposes.")
    console.print("\nPlease enter your user ID and key, as provided to you by your interviewer.")

    # console.print("ChatGPT CLI", style="bold")
    # console.print(f"Model in use: [green bold]{config['model']}")

    # Add the system message for code blocks in case markdown is enabled in the config file
    if config["markdown"]:
        add_markdown_system_message()

    # Context from the command line option
    if context:
        for c in context:
            # console.print(f"Context file: [green bold]{c.name}")
            messages.append({"role": "system", "content": c.read().strip()})

    console.rule()

    # get user id and interview key from user
    # then validate
    candidate_id = input("User ID: ")
    interview_key = input("Interview Key: ")
    verify_interview_key(candidate_id, interview_key)
    while True:
        try:
            start_prompt(session, config)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break


if __name__ == "__main__":
    main()
