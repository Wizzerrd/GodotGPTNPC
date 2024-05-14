import os
from flask import Flask
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/")

def hello_world():
    return "<p>hello world</p>"