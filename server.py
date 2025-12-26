import json
import asyncio
import numpy as np  # <--- NEW
import joblib       # <--- NEW
import google.generativeai as genai
from fastapi import FastAPI, WebSocket
from kafka import KafkaConsumer
from contextlib import asynccontextmanager
from dotenv import load_dotenv  # <--- NEW

# ==========================
# 1. CONFIGURATION
# ==========================

# Load environment variables from .env file
load_dotenv()

# Get the API Key securely
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ ERROR: GEMINI_API_KEY not found. Please create a .env file.")

genai.configure(api_key=API_KEY)
model_ai = genai.GenerativeModel('gemini-2.5-flash')

# LOAD ML MODEL <--- NEW
print("🧠 Loading ML Model...")
try:
    fraud_model = joblib.load("fraud_model.pkl")
    print("✅ ML Model Loaded Successfully!")
except:
    print("❌ ERROR: Could not load 'fraud_model.pkl'. Did you run train_model.py?")
    fraud_model = None

# ==========================
# 2. AI & KAFKA LOGIC
# ==========================
def get_ai_analysis(transaction):
    """Asks Gemini to explain the fraud."""
    try:
        # Debug print
        print(f"🤖 asking AI about TX-{transaction['transaction_id'][:8]}...")
        
        prompt = f"""
        Analyze this suspicious transaction: {json.dumps(transaction)}. 
        The ML Model flagged this as an anomaly (Outlier).
        
        Output a short "Security Protocol" log style. 
        Format:
        > CRITICAL FLAG: [Reason]
        > DEVICE MISMATCH: [Details]
        > Recommendation: [Action]
        """
        response = model_ai.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "> SYSTEM ERROR: AI Unresponsive."

async def kafka_consumer_engine(websocket: WebSocket):
    """Reads Kafka and pushes to WebSocket."""
    consumer = KafkaConsumer(
        'transactions',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest'
    )

    print("🚀 Backend connected to Kafka. Listening...")

    try:
        for message in consumer:
            data = message.value
            
            # ----------------------------------------
            # ML PREDICTION LOGIC <--- NEW
            # ----------------------------------------
            is_fraud = False
            
            if fraud_model:
                # Prepare data for model (2D array: [[amount]])
                features = np.array([[data['amount']]])
                # Predict: 1 = Normal, -1 = Anomaly
                prediction = fraud_model.predict(features)[0]
                
                if prediction == -1:
                    is_fraud = True
                    print(f"⚠️ ML Model flagged transaction: ${data['amount']}")
            else:
                # Fallback if model failed to load
                if data['amount'] > 3000:
                    is_fraud = True

            # ----------------------------------------
            
            payload = {
                "id": data['transaction_id'][:8],
                "time": data['timestamp'].split('T')[1][:-1],
                "amount": data['amount'],
                "user": f"User_{data['user_id']}",
                "location": data['location'],
                "status": "SAFE",
                "ai_analysis": ""
            }

            if is_fraud:
                payload['status'] = "WARNING"
                # Ask AI for explanation
                payload['ai_analysis'] = get_ai_analysis(data)
            
            await websocket.send_json(payload)
            await asyncio.sleep(0.01)
            
    except Exception as e:
        print(f"Error: {e}")

# ==========================
# 3. FASTAPI WEBSOCKET
# ==========================
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("🔌 Frontend Client Connected!")
    await websocket.accept()
    await kafka_consumer_engine(websocket)