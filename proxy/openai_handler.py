import os
from openai import OpenAI, AssistantEventHandler

class EventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def on_text_created(self, text):
        self.messages.append(text.value)  # Ensure only the string value is appended
        print(f"\nassistant > {text.value}", flush=True)
      
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
      
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]

assistant = client.beta.assistants.create(
    name="Surveillance Agent",
    instructions="You are a pirate. Arr!",
    model="gpt-4o",
)
thread = client.beta.threads.create()

def speech_to_text(audio_file_path):
    """Converts speech from an audio file to text using OpenAI's Whisper model."""
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(audio_file_path, "rb"),
        language="en"
    )
    print(response)
    return response.text

def send_message(message):
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )
    event_handler = EventHandler()
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=assistant.instructions,
        event_handler=event_handler,
    ) as stream:
        for _ in stream:
            pass  # This line ensures the stream runs to completion

    for msg in event_handler.messages:
        yield msg
