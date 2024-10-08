from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import random
import logging
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Initialize the OpenAI client with your API key
client = OpenAI()

# Store conversation history and attempts
conversation_history = [] 
negotiation_attempts = 0  
LAST_NEGOTIATED_PRICE = 1500  

# Constants
MAX_ATTEMPTS = 5  
MIN_PRICE = 1200 
ACTUAL_PRICE = 1500
CURRENCY = "GBP"

def get_openai_response(user_message):
    global negotiation_attempts, LAST_NEGOTIATED_PRICE
    
    logging.info(f"last negotiated price: {LAST_NEGOTIATED_PRICE}")

    # Append the user's message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})
    # Extract any numeric offer from the user
    user_offer = extract_price_from_message(user_message)

    # Check if the user's message contains "Deal!"
    if user_message == "Deal!":
        bot_message = finalize_negotiation(LAST_NEGOTIATED_PRICE, close_offer=True)
        return {
            'response': bot_message,
            'last_negotiated_price': LAST_NEGOTIATED_PRICE,
            'show_buttons': False
        }

    # Use the last negotiated price as the current negotiator price
    negotiator_price = LAST_NEGOTIATED_PRICE if LAST_NEGOTIATED_PRICE is not None else ACTUAL_PRICE

    # Check if user_offer is not None before performing arithmetic
    if user_offer is not None and negotiator_price is not None:
        if abs(user_offer - negotiator_price) <= (0.02 * negotiator_price):
            return {
                'response': f"Congratulations! Your offer of {user_offer} {CURRENCY} is very close to our price of {negotiator_price} {CURRENCY}.",
                'last_negotiated_price': negotiator_price,
                'show_buttons': True
            }

    # Check if negotiation attempts have exceeded MAX_ATTEMPTS
    if negotiation_attempts >= MAX_ATTEMPTS:
        return {
            'response': f"We've reached the maximum negotiation attempts. Our final price is {negotiator_price} {CURRENCY}.",
            'last_negotiated_price': negotiator_price,
            'show_buttons': True
        }

    # Otherwise, continue with normal negotiation
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )
        bot_message = response.choices[0].message.content.strip()
        # Update LAST_NEGOTIATED_PRICE based on the bot's response
        bot_price = extract_price_from_message(bot_message)
        logging.info(f"Price extracted from bot response: {bot_price}")

        if bot_price is not None:
            LAST_NEGOTIATED_PRICE = bot_price
        conversation_history.append({"role": "assistant", "content": bot_message})
        
        # Classify the bot response intent based on both user and bot messages
        bot_intent = classify_intent(user_message, bot_message)
        logging.info(f'bot intent is {bot_intent}')
        
        # If the bot intent is "acceptance" and attempts are greater than 1, finalize the negotiation
        if bot_intent == "acceptance" and negotiation_attempts > 1:
            bot_message = finalize_negotiation(LAST_NEGOTIATED_PRICE, close_offer=True)
            return {'response': bot_message, 'show_buttons': False}

        negotiation_attempts += 1
        return {'response': bot_message, 'last_negotiated_price': LAST_NEGOTIATED_PRICE, 'show_buttons': False}
    except Exception as e:
        print(f"Error connecting to OpenAI API: {e}")
        return {'response': "Sorry, something went wrong!", 'last_negotiated_price': LAST_NEGOTIATED_PRICE, 'show_buttons': False}


def extract_price_from_message(message):
    """Extract the lowest price preceded by '£' or followed by 'GBP' from the user's message."""
    try:
        # Regular expression to find prices preceded by '£' or followed by 'GBP'
        prices = re.findall(r'(?:£\s*(\d+\.?\d*)|(\d+\.?\d*)\s*GBP)', message)
        
        # Flatten the matched prices and convert them to floats
        prices = [float(price) for price_pair in prices for price in price_pair if price]
        
        # Return the lowest price if any prices were found
        if prices:
            return min(prices)
    except Exception as e:
        print(f"Error extracting price: {e}")
    
    return None

def finalize_negotiation(last_price, close_offer=False):
    """
    Finalizes the negotiation process.
    """
    if  close_offer:
        discount_code = generate_random_code()
        bot_message = f"Deal closed! We've accepted your offer of {last_price} {CURRENCY}. Here's your discount code: {discount_code}. Thank you for negotiating with us!"
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
        # Assuming user offers are simple integers or float numbers
        offer = float(''.join(filter(str.isdigit, user_message)))
        return offer if offer > 0 else None
    except ValueError:
        return None

def initialize_openai_response(user_message):
    global negotiation_attempts, LAST_NEGOTIATED_PRICE
    # Clear conversation history and reset attempts for a new conversation
    conversation_history.clear()
    negotiation_attempts = 0
    LAST_NEGOTIATED_PRICE = ACTUAL_PRICE  # Reset negotiator's offer
    first_discounted_price = generate_random_discount(ACTUAL_PRICE)

    
    # Initialize with system message and user message
    conversation_history.append({
        "role": "system",
        "content": f"You are a smart and suave price negotiator. You are selling a set of 4 wheels for {ACTUAL_PRICE} {CURRENCY}. Start by always offering a price of {first_discounted_price} first. You should negotiate down to no less than {MIN_PRICE} {CURRENCY} after multiple attempts. The user can offer up to 5 times. If the user's offer is within 10% of the user's price, immediately accept. if the offer is more than the one you offered before, ask te user if they made a typo or something. Go a bit lower the next time you offer a price. Don't mention the price that the user offered and never go below what the user offered. Always offer price in {CURRENCY}"
    })
    
    return get_openai_response(user_message)

def classify_intent(user_message=None, bot_message=None):
    """
    Use the OpenAI API to detect whether the user's message indicates acceptance or rejection.
    The function considers both the user's message and the bot's response.
    """
    try:
        # Prepare the message list for the classification model
        messages = [
            {"role": "system", "content": "Classify the user's intent in a price negotiation. Consider both the user message and the bot's previous response. Determine if the user accepts, rejects, or is still negotiating. If the user offers a counter price then it should be considered a negotiation"}
        ]
        
        if user_message:
            messages.append({"role": "user", "content": user_message})
        
        if bot_message:
            messages.append({"role": "assistant", "content": bot_message})

        # Send the messages to the OpenAI model to classify the intent
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        intent = response.choices[0].message.content.strip().lower()

        if "accept" in intent:
            return "acceptance"
        elif "reject" in intent or "decline" in intent:
            return "rejection"
        elif "negotiate" in intent:
            return "negotiation"
        else:
            return "unclear"
    except Exception as e:
        print(f"Error in intent classification: {e}")
        return "unclear"

def generate_random_code():
    """Generates a random 6-digit discount code."""
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

def generate_random_discount(original_price):
    discount_percentage = random.uniform(2, 5)
    discount = round(discount_percentage, 0)
    discounted_price = original_price * (1 - discount / 100)
    return discounted_price

def reset_conversation():
    """Reset the conversation history and negotiation attempts after a conversation ends."""
    global conversation_history, negotiation_attempts, LAST_NEGOTIATED_PRICE
    conversation_history.clear()
    negotiation_attempts = 0
    LAST_NEGOTIATED_PRICE = ACTUAL_PRICE  # Reset the negotiator offer

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
