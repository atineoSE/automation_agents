import json
import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client
client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))


system_prompt = """You are an automation expert. Generate PyAutoGUI code based on user prompts.

If you need to use Spotlight on Mac use this workaround:
```
with pyautogui.hold("command"):
    time.sleep(1)
    pyautogui.press("space")
```
"""
# Workaround as described here:
# https://github.com/asweigart/pyautogui/issues/687#issuecomment-1099743127

user_prompt = """"Write PyAutoGUI code to perform the following action on {platform}.
<ACTION>
{action}
</ACTION>

Generate your response as:
* Code, delimited between <CODE> tags
* Explanation, delimited between <EXPLANATION> tags.
"""


def query(action: str) -> tuple[str | None, str | None]:
    # Force structured output by using answer prefill
    # See https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency#prefill-claudes-response and
    # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags#example-legal-contract-analysis
    messages = [
        {
            "role": "user",
            "content": user_prompt.format(platform=sys.platform, action=action),
        }
    ]
    opening_tag = "<CODE>"
    closing_tag = "</EXPLANATION>"
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
        response = opening_tag + response.split(closing_tag)[0] + closing_tag
        # print(response)
        code = (response.split("<CODE>")[-1]).split("</CODE>")[0]
        explanation = (response.split("<EXPLANATION>")[-1]).split("</EXPLANATION>")[0]

        return code, explanation
    except Exception as e:
        print(f"Error getting code from API: {str(e)}")
        return None, None


def main():
    while True:
        # Get user prompt
        print("\nEnter your task prompt (e.g. 'use the calculator to multiply 2*3')")
        action = input("> ")
        if len(action) == 0:
            action = "use the calculator to multiply 2*3"
            print(action)

        # Get code from API
        code, explanation = query(action)

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
