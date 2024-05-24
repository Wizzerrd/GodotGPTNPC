from flask import Flask, request, Response, jsonify
from openai_handler import create_characters, send_message_to_character, create_thread_on_character

app = Flask(__name__)
create_characters()

# Flask Generator Function
def character_response_generator(character_name, message):
        try:
            for chunk in send_message_to_character(character_name, message):
                # Ensure each chunk is encoded as bytes
                yield chunk.encode('utf-8')
        except Exception as e:
            yield f"Error: {str(e)}".encode('utf-8')

@app.route("/")
def hello_world():
    return "<p>hello world</p>"

@app.route("/characters/<path:character_name>/threads", methods=["POST", "GET"])
def character_threads_handler(character_name):
    match request.method:
        case "POST": return character_threads_post(character_name)
        case "GET": return character_threads_get(character_name)
        case _: return jsonify({"error": f"Invalid HTTP Method (Expected 'GET' or 'POST'. Got {request.method})"}), 422
        
def character_threads_get(character_name):
    pass

def character_threads_post(character_name):
    try:
        return create_thread_on_character(character_name)
    except Exception as e:
        yield f"Error: {str(e)}".encode('utf-8')

@app.route("/characters/<path:character_name>/messages", methods=["POST", "GET"])
def character_messages_handler(character_name):
    match request.method:
        case "POST": return character_messages_post(character_name)
        case "GET": return character_messages_get(character_name)
        case _: return jsonify({"error": f"Invalid HTTP Method (Expected 'GET' or 'POST'. Got {request.method})"}), 422

def character_messages_get(character_name):
    pass

def character_messages_post(character_name):
    body = request.json
    if not body or "message" not in body:
        return jsonify({"error": "No message in request"}), 422
    message = body["message"]
    return app.response_class(character_response_generator(character_name, message), mimetype='text/csv')

# old
    
@app.route("/messages", methods=["POST"])
def post_message():
    body = request.json
    if not body or "message" not in body:
        return jsonify({"error": "No message in request"}), 422
    message = body["message"]
    return app.response_class(character_response_generator(message), mimetype='text/csv')

if __name__ == "__main__":
    app.run(debug=True)
