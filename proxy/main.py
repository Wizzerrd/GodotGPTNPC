from flask import Flask, request, Response, jsonify
from openai_handler import send_message

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>hello world</p>"

@app.route("/messages", methods=["POST"])
def post_message():
    body = request.json
    if not body or "message" not in body:
        return jsonify({"error": "No message in request"}), 422
    
    message = body["message"]
    
    def generate():
        try:
            for chunk in send_message(message):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"
    
    return Response(generate(), content_type='text/plain')

if __name__ == "__main__":
    app.run(debug=True)
