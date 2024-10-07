from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import random

app = Flask(__name__)
CORS(app)

# Initialize the OpenAI client with your API key
client = OpenAI()

# Store conversation history and attempts
conversation_history = []  # This will reset when the server restarts
negotiation_attempts = 0  # Count of negotiation attempts

# Constants
MAX_ATTEMPTS = 7  # Set the maximum number of negotiation attempts
MIN_PRICE = 1200  # Minimum negotiable price (20% lower than 1500 GBP)
ACTUAL_PRICE = 1500  # Actual price of the product
NEGOTIATOR_OFFER = ACTUAL_PRICE  # Current offer from the negotiator

def get_openai_response(user_message):
    global negotiation_attempts

    # Append the user's message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Extract any numeric offer from the user
    user_offer = extract_price_from_message(user_message)

    # Negotiator's price logic (modify this to your own needs)
    negotiator_price = calculate_negotiator_price(negotiation_attempts)

    # Check if the user's offer is within 10% margin of negotiator's price
    if user_offer and abs(user_offer - negotiator_price) <= (0.05 * negotiator_price):
        return {
            'response': f"Congratulations! Your offer is very close to our price of {negotiator_price} GBP.",
            'show_buttons': True
        }

    # Check if negotiation attempts have exceeded MAX_ATTEMPTS
    if negotiation_attempts >= MAX_ATTEMPTS:
        return {
            'response': f"We've reached the maximum negotiation attempts. Our final price is {negotiator_price} GBP.",
            'show_buttons': True
        }

    # Otherwise, continue with normal negotiation
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )
        bot_message = response.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": bot_message})
        negotiation_attempts += 1
        return {'response': bot_message, 'show_buttons': False}
    except Exception as e:
        print(f"Error connecting to OpenAI API: {e}")
        return {'response': "Sorry, something went wrong!", 'show_buttons': False}

def extract_price_from_message(message):
    """Extract a numeric price from the user's message, if provided."""
    try:
        # Basic price extraction from message
        words = message.split()
        for word in words:
            if word.isdigit():
                return int(word)
    except Exception as e:
        print(f"Error extracting price: {e}")
    return None

def calculate_negotiator_price(attempts):
    """Logic to calculate the negotiator's price based on the number of attempts."""
    discount_rate = min(0.05 * attempts, 0.3)  # Example: 5% per attempt, up to 30%
    return ACTUAL_PRICE * (1 - discount_rate)

def finalize_negotiation(user_message, close_offer=False):
    """
    Finalizes the negotiation process.
    """
    user_intent = classify_intent(user_message)
    if user_intent == "acceptance" or close_offer:
        discount_code = generate_random_code()
        bot_message = f"Deal closed! Here's your discount code: {discount_code}. Thank you for negotiating with us!"
    else:
        bot_message = "No deal reached. Thank you for your time!"

    reset_conversation()
    return bot_message

def extract_user_offer(user_message):
    """
    Extracts a price offer from the user's message, if present.
    Returns None if no valid offer is found.
    """
    try:
        offer = float(''.join(filter(str.isdigit, user_message)))
        return offer if offer > 0 else None
    except ValueError:
        return None

def initialize_openai_response(user_message):
    global negotiation_attempts, NEGOTIATOR_OFFER
    # Clear conversation history and reset attempts for a new conversation
    conversation_history.clear()
    negotiation_attempts = 0
    NEGOTIATOR_OFFER = ACTUAL_PRICE  # Reset negotiator's offer
    
    # Initialize with system message and user message
    conversation_history.append({
        "role": "system",
        "content": f"You are a smart negotiator offering a set of 4 wheels for {ACTUAL_PRICE} GBP. Start by offering a 5% discounted price. You should negotiate down to no less than {MIN_PRICE} GBP after multiple attempts. The user can offer up to 5 times. If the user's offer is within 10% of the negotiator's price, immediately accept."
    })
    
    return get_openai_response(user_message)

def classify_intent(user_message):
    """
    Use the OpenAI API to detect whether the user's message indicates acceptance or rejection.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify the user's response as acceptance or rejection of a price negotiation."},
                {"role": "user", "content": user_message}
            ]
        )
        intent = response.choices[0].message.content.strip().lower()

        if "accept" in intent:
            return "acceptance"
        elif "reject" in intent or "decline" in intent:
            return "rejection"
        else:
            return "unclear"
    except Exception as e:
        print(f"Error in intent classification: {e}")
        return "unclear"

def generate_random_code():
    """Generates a random 6-digit discount code."""
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

def reset_conversation():
    """Reset the conversation history and negotiation attempts after a conversation ends."""
    global conversation_history, negotiation_attempts, NEGOTIATOR_OFFER
    conversation_history.clear()
    negotiation_attempts = 0
    NEGOTIATOR_OFFER = ACTUAL_PRICE  # Reset the negotiator offer

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_message = data['message']
    bot_response = get_openai_response(user_message)
    return jsonify(bot_response)  # Directly jsonify the dictionary response

@app.route('/initialize', methods=['POST'])
def chatbot_initialize():
    data = request.get_json()
    user_message = data['message']
    bot_response = initialize_openai_response(user_message)
    return jsonify(bot_response)  # Directly jsonify the dictionary response

if __name__ == '__main__':
    app.run(debug=True)
