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
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE characters (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            );
        """)
    except: print("Characters Table already exists")
    try:
        cur.execute("""
            CREATE TABLE memories (
            id SERIAL PRIMARY KEY,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            interacting_character_id INTEGER NOT NULL REFERENCES characters(id),
            thread_id INTEGER NOT NULL,
            interaction_order INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR NOT NULL
            );
        """)
    except: print("Memories Table already exists")
    conn.commit()
    cur.close()

def add_character_to_tables(conn, character_name):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO characters (name) VALUES (%s);
    """, (character_name,))
    cur.close()

def create_table_for_character(conn, character_name):
    cur = conn.cursor()
    conn.commit()
    cur.close()

conn = connect_to_db()
register_vector(conn)
# create_tables(conn)
cur = conn.cursor()
cur.execute("""SELECT * FROM characters;""")
print(cur.fetchall())
