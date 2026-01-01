import google.generativeai as genai

# =========================================================
# PASTE YOUR NEW API KEY INSIDE THE QUOTES BELOW
# =========================================================
MY_API_KEY = "AIzaSyCYNm6B6YjxoUi3rmDVNmRGMCFo4FlOEyU"

# Setup
genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Start a chat session with history memory
chat_session = model.start_chat(history=[])

print("--------------------------------------------------")
print("AI CHATBOT READY! (Type 'quit' or 'exit' to stop)")
print("--------------------------------------------------")

while True:
    user_input = input("You: ")
    
    # Check if user wants to stop
    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("Bot: Goodbye! Have a great day.")
        break

    try:
        # Send message and get response
        response = chat_session.send_message(user_input)
        print(f"Bot: {response.text}")
        print("-" * 30)
        
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        print("Make sure your API key is correct and you have internet.\n")