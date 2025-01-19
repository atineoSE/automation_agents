import json
import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client
client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))


def clean_code_block(text):
    # Remove triple backticks and language identifier
    lines = text.split("\n")
    cleaned_lines = []
    in_code_block = False

    for line in lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line.startswith("```"):
            cleaned_lines.append(line)

    # Join lines with escaped newlines
    return "\\n".join(cleaned_lines)


def get_code_from_api(prompt) -> tuple[str | None, str | None]:
    system_prompt = """You are an automation expert. Generate PyAutoGUI code based on user prompts.
    Provide response in JSON format as follows:
    {
    "code": "The python code which implements the user request"
    "explanation": "The explanation of how the script works"
    }
    """

    user_prompt = (
        f"Write PyAutoGUI code to {prompt} on {sys.platform}. Produce valid JSON."
    )

    # Force structured output by using answer prefill
    # See https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency#prefill-claudes-response and
    # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags#example-legal-contract-analysis
    messages = [{"role": "user", "content": user_prompt}]
    opening_tag = "{"
    closing_tag = "}"
    messages.append({"role": "assistant", "content": opening_tag})

    try:
        message = client.messages.create(
            # model="claude-3-5-haiku-latest",
            model="claude-3-5-sonnet-latest",
            max_tokens=8192,  # As per limit here: https://docs.anthropic.com/en/docs/about-claude/models
            system=system_prompt,
            messages=messages,
            temperature=0.0,
        )
        response = message.content[0].text
        structured_response = opening_tag + response.split(closing_tag)[0] + closing_tag
        cleaned_response = clean_code_block(structured_response)

        print(f"Cleaned responses: {cleaned_response}")

        # Parse JSON from response
        result = json.loads(cleaned_response)
        return result["code"], result["explanation"]
    except Exception as e:
        print(f"Error getting code from API: {str(e)}")
        return None, None


def main():
    while True:
        # Get user prompt
        print("\nEnter your task prompt (e.g. 'use the calculator to multiply 2*3')")
        user_prompt = input("> ")
        if len(user_prompt) == 0:
            user_prompt = "use the calculator to multiply 2*3"
            print(user_prompt)

        # Get code from API
        code, explanation = get_code_from_api(user_prompt)

        if not code:
            print("Failed to generate code. Please try again.")
            continue

        # Display generated code
        print("\nHere is the code generated for your prompt:")
        print("\nCode explanation:\n", explanation)
        print("\nGenerated code:\n")
        print(code)

        # Get user decision
        while True:
            print(
                "\nWould you like to execute this code (yes/no) or modify the prompt (modify)?"
            )
            user_decision = input("> ").lower()

            if user_decision == "yes":
                try:
                    print("\nExecuting code...")
                    exec(code)
                    print("Execution complete.")
                    return
                except Exception as e:
                    print(f"\nError during execution: {str(e)}")

            elif user_decision == "modify":
                break
            elif user_decision == "no":
                return
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'modify'")


if __name__ == "__main__":
    main()
