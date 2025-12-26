import time
import json
import random
import numpy as np
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

print("✅ Stream Started: 1 TX every 5 seconds...")

try:
    while True:
        # DECIDE TYPE
        # 95% Safe (Matches Training Data)
        # 5% Fraud (Outliers)
        if random.random() < 0.95:
            # SAFE: Normal distribution centered at $50
            amount = np.random.normal(loc=50, scale=15)
            amount = round(abs(amount), 2)
            status_label = "SAFE"
        else:
            # FRAUD: Random high value
            amount = round(random.uniform(2000.0, 9000.0), 2)
            status_label = "⚠️ FRAUD"

        transaction = {
            "transaction_id": fake.uuid4(),
            "user_id": fake.random_int(min=1000, max=1010),
            "amount": amount,
            "currency": "USD",
            "merchant_id": fake.uuid4(),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "location": fake.city()
        }

        producer.send('transactions', value=transaction)
        print(f"Sent: ${amount} ({status_label})")
        time.sleep(5)

except KeyboardInterrupt:
    producer.close()