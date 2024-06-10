import os, time, yaml

from os import listdir
from os.path import isfile, join
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk, ChatCompletion

from postgres_handler import connect_to_db, add_character_to_table, add_memory_to_character, retrieve_relevant_memories

load_dotenv()
client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]
language_model = os.environ["LANGUAGE_MODEL"]
embeddings_model = os.environ["EMBEDDINGS_MODEL"]

characters = {}
conn = connect_to_db()
directory = "characters/"

def create_characters():
    add_character_to_table(conn, "player")
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    if not files:  return ("No files found", 404)
    for file in files:
        with open(directory+file, 'r') as data:
            ref = file.split(".yaml")[0]
            characters[ref] = {"threads":{}}
            try: add_character_to_table(conn, ref)
            except: print("Ref already in table: ", (ref))

def create_thread_on_character_with_character(pov_ref, oth_ref):
    closed = close_thread_on_character_with_character(pov_ref, oth_ref)
    if closed: return closed
    name = ""
    background = ""
    with open(directory+pov_ref+".yaml", 'r') as file:
        data = yaml.safe_load(file)
        name=data['name']
        background=data['background']
    characters[pov_ref]["threads"][oth_ref] = []
    thread = characters[pov_ref]["threads"][oth_ref]
    prompt = f"""
        This LLM represents the character {pov_ref} and will generate dialogue interactions between it and the character {oth_ref}
        Your name is {name}
        Background: {background}
    """
    thread.append({"role":"system","content":prompt})
    return ("Thread created successfully on ref " + pov_ref, " with ", oth_ref, 200)

def close_thread_on_character_with_character(pov_ref, oth_ref):
    if not pov_ref in characters:  return ("POV Character ref not found for " + pov_ref, 404)
    if oth_ref != "player" and not oth_ref in characters:  return ("Interacting Character ref not found for " + oth_ref, 404)
    pov_character = characters[pov_ref]
    if not oth_ref in pov_character["threads"]: 
        print("Thread not found between " + pov_ref + " and  " + oth_ref)
        return False
    thread = pov_character["threads"][oth_ref]
    if thread:
        summary_prompt = "Generate a summary of this conversation between you and " + oth_ref
        thread.append({"role":"system","content": summary_prompt})
        api_response = client.chat.completions.create(
            model=language_model,
            messages=thread
        )
        thread.pop()
        summary = api_response.choices[0].message.content
        embedding = client.embeddings.create(input="Conversation With: " + oth_ref + "\nContent:\n" + str(thread), model=embeddings_model).data[0].embedding
        interaction = {"pov_ref":pov_ref, "oth_ref":oth_ref, "content":thread, "summary":summary, "embedding":embedding}
        add_memory_to_character(conn, interaction)
    return False

def send_message_to_character(character_ref, message, streaming):
    if not character_ref in characters: return ("Character ref not found for " + character_ref, 404)
    character = characters[character_ref]
    threads = character["threads"]
    thread = threads["player"]
    thread.append({"role":"user", "content":message})
    enriched_text = f"""
    Interacting Character: player
    Message: {message}
    """
    embedding = client.embeddings.create(input=enriched_text, model=embeddings_model).data[0].embedding
    memories = retrieve_relevant_memories(conn, character_ref, "player", embedding)
    memory_prompt = "Relevant memories:\n"
    for content, similarity, summary in memories:
        memory_prompt += f"{summary}\n"
    thread.append({"role":"system","content":memory_prompt})
    if streaming:
        with client.chat.completions.create(
            model=language_model,
            stream=True,
            messages=thread
        ) as stream:
            response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta: response += delta
                # yield chunk
            thread.pop()
            print(response)
            thread.append({"role":"assistant", "content":response})
    else:
        api_response = client.chat.completions.create(
            model=language_model,
            messages=thread
        )
        response = api_response.choices[0].message.content
        thread.pop()
        thread.append({"role":"assistant", "content":response})
        print(response)
        return response

create_characters()
# create_thread_on_character_with_character("knight", "player")
# send_message_to_character("knight", "I like bananas", True)
create_thread_on_character_with_character("knight", "player")
send_message_to_character("knight", "I live in a cave", True)
create_thread_on_character_with_character("knight", "player")
send_message_to_character("knight", "Do you know where I live?", True)


