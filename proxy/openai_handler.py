import os
from os import listdir
from os.path import isfile, join

from dotenv import load_dotenv
from openai import OpenAI, AssistantEventHandler

class EventHandler(AssistantEventHandler):
    def on_text_created(self, text): 
        print(f"\nassistant > ", flush=True)
      
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
                        print(f"{output.logs}", flush=True)

load_dotenv()
client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]

characters = {}

def create_characters():
    directory = "characters/"
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    if not files:  return ("No files found", 404)
    for file in files:
        with open(directory+file, 'r') as data:
            ref = file.split(".yaml")[0]
            character = client.beta.assistants.create(
                name=ref,
                instructions=data.read(),
                model="gpt-4o",
            )
            characters[ref] = {"assistant":character,"threads":[]}
            

def create_thread_on_character(character_ref):
    if not character_ref in characters:  return ("Character ref not found for " + character_ref, 404)
    character = characters[character_ref]
    thread = client.beta.threads.create()
    character["threads"].append(thread)
    return ("Thread created successfully on ref " + character_ref, 200)

def send_message_to_character(character_ref, message, streaming):
    if not character_ref in characters: return ("Character ref not found for " + character_ref, 404)
    character = characters[character_ref]
    threads = character["threads"]
    if not threads: return ("No threads on character ref " + character_ref, 404)
    thread = character["threads"][-1]
    assistant = character["assistant"]
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )
    if streaming:
        # event_handler = EventHandler()
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=assistant.instructions,
            # event_handler=event_handler,
        ) as stream:
            for chunk in stream:
                if hasattr(chunk.data, "delta"):
                    yield chunk.data.delta.content[0].text.value
    else:
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=assistant.instructions
        )
        res = {}
        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            res["content"] = messages.data[0].content[0].text.value
        else:  res["content"] = "Could not complete request to OpenAI"
        res["stream-status"] = 'streaming'
        yield res

def speech_to_text(audio_file_path):
    """Converts speech from an audio file to text using OpenAI's Whisper model."""
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(audio_file_path, "rb"),
        language="en"
    )
    return response.text