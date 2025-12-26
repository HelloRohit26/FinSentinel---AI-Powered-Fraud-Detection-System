import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

print("📊 Generating consistent training data...")

# 1. Create 'Normal' Data (Bell Curve centered at $50)
# Most data will be between $0 and $100.
# We generate 5000 points.
X_train = np.random.normal(loc=50, scale=15, size=(5000, 1))

# Ensure no negative values (can't have negative spending)
X_train = np.abs(X_train)

# 2. Train Model
# contamination=0.01: We are very strict. Only top 1% outliers are fraud.
print("🧠 Training Isolation Forest...")
model = IsolationForest(contamination=0.01, random_state=42)
model.fit(X_train)

# 3. Test Validation
print("\n🧪 Testing Logic:")
print(f"   $45.50 (Normal) -> {model.predict([[45.50]])[0]} (Should be 1)")
print(f"   $85.00 (Normal) -> {model.predict([[85.00]])[0]} (Should be 1)")
print(f"   $5000.00 (Fraud) -> {model.predict([[5000.00]])[0]} (Should be -1)")

joblib.dump(model, "fraud_model.pkl")
print("\n✅ New Model Saved!")