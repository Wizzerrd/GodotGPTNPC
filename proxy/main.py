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
                # Ensure each chunk is encoded as bytes
                yield chunk.encode('utf-8')
        except Exception as e:
            yield f"Error: {str(e)}".encode('utf-8')
    
    return app.response_class(generate(), mimetype='text/csv')

if __name__ == "__main__":
    app.run(debug=True)
