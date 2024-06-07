import os

from postgres_handler import connect_to_db, add_character_to_table, add_memory_to_character_with_character
from os import listdir
from os.path import isfile, join
from dotenv import load_dotenv
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.assistant_stream_event import ThreadMessageCompleted, ThreadMessageDelta

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
conn = connect_to_db()

def create_characters():
    try: add_character_to_table("player")
    except: print("Ref already in table: player")
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
            try: add_character_to_table(ref)
            except: print("Ref already in table: ", (ref))

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
    res = {"character_ref":character_ref, "stream-status":"streaming"}
    if streaming:
        # event_handler = EventHandler()
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=assistant.instructions,
            # event_handler=event_handler,
        ) as stream:
            for chunk in stream:
                if isinstance(chunk, ThreadMessageDelta) and hasattr(chunk.data, "delta"):
                    delta = chunk.data.delta.content[0].text.value
                    res["content"] = delta
                    yield res
                if isinstance(chunk, ThreadMessageCompleted):
                    # weird shit going on right here
                    try:
                        add_memory_to_character_with_character(conn, {
                            "pov_character_ref": character_ref,
                            "oth_character_ref": "player",
                            "thread_id": len(threads)-1,
                            "speaking": True,
                            "content": chunk.data.content[0].text.value,
                            "embedding": client.embeddings.create(input=message, model="text-embedding-3-small")
                        })
                    except:
                        pass
                    
    else:
        message = ""
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=assistant.instructions
        )
        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            message = messages.data[0].content[0].text.value
            res["content"] = message
            add_memory_to_character_with_character(conn, {
                "pov_character_ref": character_ref,
                "oth_character_ref": "player",
                "thread_id": len(threads)-1,
                "speaking": True,
                "content": message,
                "embedding": client.embeddings.create(input=message, model="text-embedding-3-small")
            })
        else:  res["content"] = "Could not complete request to OpenAI"
        yield res
