import json
from flask import Flask, request, jsonify
from openai_handler import create_characters, send_message_to_character, create_thread_on_character

app = Flask(__name__)
create_characters()

# Flask Generator Function
def character_response_generator(character_name, message, streaming):
        try:
            yield json.dumps({"stream-status":"starting", "content":f"stream started for {character_name}", "character-ref":character_name})
            for chunk in send_message_to_character(character_name, message, streaming):
                if isinstance(chunk, dict): 
                    print(chunk)
                    chunk["character-ref"] = character_name
                    yield json.dumps(chunk)
                    # print(chunk)
                else:
                # Ensure each chunk is encoded as bytes
                    yield json.dumps({"stream-status":"streaming", "content":chunk, "character-ref":character_name})
            yield json.dumps({"stream-status":"stopping", "content":f"stream stopping for {character_name}", "character-ref":character_name})
        except Exception as e:
            yield f"Error: {str(e)}".encode('utf-8')

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
        result, status_code = create_thread_on_character(character_name)
        return jsonify({"message": result, "thread-status": "created"}), status_code
    except Exception as e:
        return jsonify({"error": str(e), "thread-status": "error"}), 500

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
    streaming = body["streaming"]
    return app.response_class(character_response_generator(character_name, message, streaming), mimetype='application/json')
