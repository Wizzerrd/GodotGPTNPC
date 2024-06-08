import psycopg2, os

from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

from openai import OpenAI, AssistantEventHandler

load_dotenv()

def connect_to_db():
    return psycopg2.connect(
        dbname="your_db_name",
        user=os.environ["PSQL_USERNAME"],
        password=os.environ["PSQL_PASSWORD"],
        host="localhost",
        port="5432",
        options='-c client_encoding=UTF8'
    )

def create_tables(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE characters (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
    except: 
        conn.rollback()
        print("Characters Table already exists")
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE memories (
            id SERIAL PRIMARY KEY,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            interacting_character_id INTEGER NOT NULL REFERENCES characters(id),
            thread_id INTEGER NOT NULL,
            speaking BOOLEAN NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR NOT NULL
            );
        """)
        conn.commit()
        cur.close()
    except: 
        conn.rollback()
        print("Memories Table already exists")

def add_character_to_table(conn, character_name):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO characters (name) VALUES (%s);
    """, (character_name,))
    conn.commit()
    cur.close()

def add_memory_to_character_with_character(conn, interaction):
    print("Getting pov id")
    print(interaction["pov_character_ref"])
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (interaction["pov_character_ref"],))
    character_id = cur.fetchall()[0][0]
    print(character_id)
    print("Getting oth id")
    cur.close()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (interaction["oth_character_ref"],))
    interacting_character_id = cur.fetchall()[0][0]
    print(interacting_character_id)
    print("Inserting...")
    cur.close()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memories (character_id, interacting_character_id, thread_id, speaking, content, embedding)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (
            character_id, 
            interacting_character_id, 
            interaction["thread_id"], 
            interaction["speaking"], 
            interaction["content"], 
            interaction["embedding"]
        )
    )
    conn.commit()
    print("Memory saved!")
    cur.close()

def retrieve_relevant_memories(conn, pov_character, oth_character, current_interaction_embedding, threshold=0.8):
    print("Retrieving relevant memories for " + pov_character)
    cur = conn.cursor()
    # Get the POV character ID
    cur.execute("""
        SELECT id FROM characters WHERE name = %s
    """, (pov_character,))
    pov_character_id = cur.fetchone()[0]
    # Get the interacting character ID
    cur.execute("""
        SELECT id FROM characters WHERE name = %s
    """, (oth_character,))
    oth_character_id = cur.fetchone()[0]
    # Convert the current interaction embedding to a string format for SQL query
    embedding_str = ','.join(map(str, current_interaction_embedding))
    # Retrieve and filter memories based on cosine similarity
    cur.execute(f"""
        SELECT content, embedding, (embedding <=> ARRAY[{embedding_str}]) as similarity
        FROM memories
        WHERE character_id = %s AND interacting_character_id = %s
        ORDER BY similarity ASC
    """, (pov_character_id, oth_character_id))
    all_memories = cur.fetchall()
    cur.close()
    # Filter memories by similarity threshold
    relevant_memories = [(content, 1 - similarity) for content, embedding, similarity in all_memories if 1 - similarity >= threshold]
    print(f"Retrieved {len(relevant_memories)} relevant memories")
    return relevant_memories

conn = connect_to_db()
cur = conn.cursor()
register_vector(conn)

create_tables(conn)
embedding = OpenAI().embeddings.create(input="My favorite pizza is pepperoni.", model="text-embedding-3-small").data[0].embedding
# add_character_to_table(conn, "knight")
# add_character_to_table(conn, "player")
# add_memory_to_character_with_character(conn, {
#     "pov_character_ref":"pirate",
#     "oth_character_ref":"player",
#     "thread_id":1,
#     "speaking":False,
#     "content":"My favorite pizza is pepperoni.",
#     "embedding":embedding
# })
