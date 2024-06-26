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
        SELECT id FROM characters WHERE name LIKE %s
    """, (character_name,))
    if cur.fetchone():
        print("Ref already in table: ", (character_name))
        cur.close()
    else:
        cur.close()
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
    print("Getting oth id")
    cur.close()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (interaction["oth_character_ref"],))
    interacting_character_id = cur.fetchall()[0][0]
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
        SELECT id FROM characters WHERE name LIKE %s
    """, (pov_character,))
    pov_character_id = cur.fetchone()[0]
    # Get the interacting character ID
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (oth_character,))
    oth_character_id = cur.fetchone()[0]
    cur.execute("""
        SELECT content, embedding <-> %s::vector as distance
        FROM memories
        WHERE character_id = %s AND interacting_character_id = %s
        ORDER BY distance ASC
    """, (current_interaction_embedding, pov_character_id, oth_character_id))
    all_memories = cur.fetchall()
    cur.close()
    print(all_memories)
    # Filter memories by similarity threshold
    relevant_memories = [(content, 1 - distance) for content, distance in all_memories if 1 - distance >= threshold]
    print(f"Retrieved {len(relevant_memories)} relevant memories")
    print(relevant_memories)
    return relevant_memories

conn = connect_to_db()
cur = conn.cursor()
register_vector(conn)

# create_tables(conn)
# embedding = OpenAI().embeddings.create(input="gooner", model="text-embedding-3-small").data[0].embedding
# retrieve_relevant_memories(conn, "knight", "player", embedding)
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
