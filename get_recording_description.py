from openadapt.db.crud import get_latest_recording, get_new_session


def main():
    # Fetch last recording
    session = get_new_session(read_only=True)
    recording = get_latest_recording(session)

    # Prompt Claude for a description of each step
    event_descriptions = [
        event.prompt_for_description() for event in recording.processed_action_events
    ]

    # Create a prompt with the description of the steps
    with open("prompt.txt", "w") as file:
        for index, description in enumerate(event_descriptions):
            file.write(f"{index+1}. {description}\n")


if __name__ == "__main__":
    main()
