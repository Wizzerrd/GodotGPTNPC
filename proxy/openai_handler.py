import os, time

from postgres_handler import connect_to_db, add_character_to_table, add_memory_to_character_with_character, retrieve_relevant_memories
from os import listdir
from os.path import isfile, join
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk, ChatCompletion

load_dotenv()
client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]
language_model = os.environ["LANGUAGE_MODEL"]
embeddings_model = os.environ["EMBEDDINGS_MODEL"]

characters = {}
conn = connect_to_db()

def create_characters():
    add_character_to_table(conn, "player")
    directory = "characters/"
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    if not files:  return ("No files found", 404)
    for file in files:
        with open(directory+file, 'r') as data:
            ref = file.split(".yaml")[0]
            characters[ref] = {"threads":[]}
            try: add_character_to_table(conn, ref)
            except: print("Ref already in table: ", (ref))

def create_thread_on_character(character_ref):
    if not character_ref in characters:  return ("Character ref not found for " + character_ref, 404)
    character = characters[character_ref]
    character["threads"].append([])
    return ("Thread created successfully on ref " + character_ref, 200)

def send_message_to_character(character_ref, message, streaming):
    if not character_ref in characters: return ("Character ref not found for " + character_ref, 404)
    character = characters[character_ref]
    threads = character["threads"]
    if not threads: return ("No threads on character ref " + character_ref, 404)
    thread = threads[-1]
    thread.append({"role":"user", "content":message})
    enriched_text = f"""
    Speaker: player

    Speaking?: False
    Message: {message}
    """
    embedding = client.embeddings.create(input=enriched_text, model=embeddings_model).data[0].embedding
    memories = retrieve_relevant_memories(conn, character_ref, "player", embedding)
    memory_prompt = "Relevant memories:\n"
    for content, similarity in memories:
        memory_prompt += f"- {content} (Similarity: {similarity:.2f})\n"
    thread.append({"role":"system","content":memory_prompt})
    # # move?
    add_memory_to_character_with_character(conn, {
                        "pov_character_ref": character_ref,
                        "oth_character_ref": "player",
                        "thread_id": len(threads)-1,
                        "speaking": False,
                        "content": message,
                        "embedding": embedding
                    })
    res = {"character_ref":character_ref, "stream-status":"streaming"}
    if streaming:
        with client.chat.completions.create(
            model=language_model,
            stream=True,
            messages=thread
        ) as stream:
            response = ""
            for chunk in stream:
                if chunk.choices[0].finish_reason:
                    enriched_text = f"""
                    Speaker: {character_ref}

                    Speaking?: True
                    Message: {response}
                    """
                    print(enriched_text)
                    embedding = client.embeddings.create(input=enriched_text, model=embeddings_model).data[0].embedding
                    add_memory_to_character_with_character(conn, {
                        "pov_character_ref": character_ref,
                        "oth_character_ref": "player",
                        "thread_id": len(threads)-1,
                        "speaking": True,
                        "content": response,
                        "embedding": embedding
                    })
                    thread.pop()       
                    # thread.pop()
                else:

                    delta = chunk.choices[0].delta.content
                    res["content"] = delta
                    response += delta
                    # yield res
    else:
        api_response = client.chat.completions.create(
            model=language_model,
            messages=thread
        )
        print(api_response)
        response = ""
        #     res["content"] = response
        #     enriched_text = f"""
        #     Speaker: {character_ref}
        #     Timestamp: {time.time()}
        #     Speaking?: True
        #     Message: {response}
        #     """
        #     embedding = client.embeddings.create(input=enriched_text, model=embeddings_model).data[0].embedding
        #     add_memory_to_character_with_character(conn, {
        #         "pov_character_ref": character_ref,
        #         "oth_character_ref": "player",
        #         "thread_id": len(threads)-1,
        #         "speaking": True,
        #         "content": message,
        #         "embedding": embedding
        #     })       
        # else:  res["content"] = "Could not complete request to OpenAI"
        # yield res

create_characters()
create_thread_on_character("pirate")
# send_message_to_character("pirate","hi", False)
send_message_to_character("pirate","My sentiment on bananas is good!", True)
create_thread_on_character("pirate")
send_message_to_character("pirate","what is my sentiment on bananas?", True)
create_thread_on_character("pirate")
send_message_to_character("pirate","do I like bananas?", True)
