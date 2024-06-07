import psycopg2, os

from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

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
    cur.execute()
    cur.close()

def add_memory_to_character_with_character(conn, interaction):
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (interaction["pov_character_ref"]))
    character_id = cur.fetchall()[0]
    cur.close()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM characters WHERE name LIKE %s
    """, (interaction["oth_character_ref"]))
    interacting_character_id = cur.fetchall()[0]
    cur.close()
    cur.execute("""
        INSERT INTO memories (character_id, interacting_character_id, thread_id, speaking, interaction_order, content, embedding)
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
    cur.commit()
    cur.close()

conn = connect_to_db()
cur = conn.cursor()
register_vector(conn)
create_tables(conn)
