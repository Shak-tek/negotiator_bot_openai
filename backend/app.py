from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)

# Initialize the OpenAI client with your API key
client = OpenAI()

# Store conversation history
conversation_history = []  # This will be reset when the server restarts

def get_openai_response(user_message):
    # Append the user's message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=conversation_history
        )

        # Get the bot's response
        bot_message = response.choices[0].message.content.strip()
        # Append the bot's message to the conversation history
        conversation_history.append({"role": "assistant", "content": bot_message})

        return bot_message

    except Exception as e:
        print(f"Error connecting to OpenAI API: {e}")
        return "Sorry, something went wrong!"

def initialize_openai_response(user_message):
    # Clear conversation history for a new conversation
    conversation_history.clear()
    
    # Initialize with system message and user message
    conversation_history.append({
        "role": "system",
        "content": "You are a smart and suave product price negotiator. Introduce yourself as a smart negotiator. Offer the customer your product. You have to provide precise and concise answers and only respond to questions related to the product price. The product is a set of 4 wheels by MAK and the color is silver and black. The price of the product is 1500 GBP. Minimum price should be 20% lower than actual price. Do not give the maximum discount on the first try. Maximum tries for getting discount are 5 after that close the conversation. Everytime customer asks you the price it should always remain within the actual price and the minimum price and it should be lower than the one you offered in the previous but never be lower than the minimum price. Also don't display the same price everytime. Don't give the max discount on the first try. Also offer the discount to the customer when they initiate the conversation and be casual and polite."
    })
    
    return get_openai_response(user_message)

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_message = data['message']
    bot_response = get_openai_response(user_message)
    return jsonify({'response': bot_response})

@app.route('/initialize', methods=['POST'])
def chatbot_initialize():
    data = request.get_json()
    user_message = data['message']
    bot_response = initialize_openai_response(user_message)
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
