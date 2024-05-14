import os, json
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/")

def hello_world():
    return "<p>hello world</p>" 
    
@app.route("/characters/<character_name>", methods=['GET'])
def get_character(character_name):
    print(character_name)
    return (character_name,200)