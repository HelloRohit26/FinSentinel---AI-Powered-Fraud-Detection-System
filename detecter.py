import json
import google.generativeai as genai
from kafka import KafkaConsumer
from dotenv import load_dotenv
import os
load_dotenv()       
# ==========================================
# 1. SETUP AI CONFIGURATION
# ==========================================
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def investigate_transaction(transaction):
    """
    Sends the suspicious transaction data to Gemini to generate a report.
    """
    print("   🤖 AI Agent is investigating...")

    prompt = f"""
    You are a Senior Financial Fraud Analyst. 
    Analyze this suspicious transaction:
    {json.dumps(transaction, indent=2)}

    The user usually spends less than $100.

    1. Explain why this looks like fraud.
    2. Assign a Risk Score (1-100).
    3. Recommend 2 immediate actions for the bank.

    Keep your response concise (bullet points).
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# ==========================================
# 2. KAFKA CONSUMER SETUP
# ==========================================
consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("🕵️  Fraud Detector AI started... waiting for transactions.")

# ==========================================
# 3. MAIN LOOP
# ==========================================
for message in consumer:
    transaction = message.value

    # TRIGGER: Amount > $3000
    if transaction['amount'] > 3000:
        print("\n" + "="*50)
        print(f"🚨 [FRAUD ALERT] High Value: ${transaction['amount']}")
        print(f"   User: {transaction['user_id']} | Loc: {transaction['location']}")

        # CALL THE AI AGENT
        report = investigate_transaction(transaction)

        print("\n📄 --- AI INVESTIGATION REPORT ---")
        print(report)
        print("="*50 + "\n")

    else:
        # Print legitimate ones on a single line to keep log clean
        print(f"✅ Legit: ${transaction['amount']}")