from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key (you can store it securely in environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key or set it as an environment variable

def get_openai_response(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Specify the model you want to use, e.g., 'gpt-4'
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error connecting to OpenAI API: {e}")
        return "Sorry, something went wrong!"

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_message = data['message']

    # Get response from OpenAI API
    bot_response = get_openai_response(user_message)

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
