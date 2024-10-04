from flask import Flask, request, jsonify
from flask_cors import CORS
import requests  # Import requests
import json

app = Flask(__name__)
CORS(app)

Ollama_API_URL = 'http://localhost:11434/api/chat'  # Adjust the port if necessary

def get_ollama_response(user_message):
    payload = {
        "model": "llama3.2",  # Replace with the actual model name
          "stream":False,
        "messages": [
    {
      "role": "user",
      "content": user_message
    }
  ]
    }
    try:
        response = requests.post(Ollama_API_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama API: {e}")
        return "Sorry, something went wrong!"

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_message = data['message']

    # Get response from Ollama LLM
    bot_response = get_ollama_response(user_message)

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
