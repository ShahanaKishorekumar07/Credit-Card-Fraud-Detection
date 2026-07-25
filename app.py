import random
from flask import Flask, render_template, request, redirect, session
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = "secret123"

USER = {"username": "admin", "password": "1234"}

otp_storage = {}
transaction_history = []
login_attempts = 0

rf_model = joblib.load('fraud_model.pkl')
iso_model = joblib.load('anomaly_model.pkl')


@app.route('/')
def login_page():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():
    global login_attempts

    if login_attempts >= 3:
        return "🚫 Too many attempts. Blocked"

    if request.form['username'] == USER["username"] and request.form['password'] == USER["password"]:
        session['user'] = USER["username"]
        login_attempts = 0
        return redirect('/home')
    else:
        login_attempts += 1
        return render_template("login.html", error="Invalid Login")


@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        values = []
        for key in request.form:
            if key != "location":
                try:
                    values.append(float(request.form[key]))
                except:
                    values.append(0.0)

        while len(values) < 30:
            values.append(0.0)

        features = np.array(values).reshape(1, -1)

        rf_pred = rf_model.predict(features)[0]
        iso_pred = iso_model.predict(features)[0]

        # 🎯 Risk Score
        risk_score = 0
        reasons = []

        if rf_pred == 1:
            risk_score += 50
            reasons.append("ML model flagged as fraud")

        if iso_pred == -1:
            risk_score += 30
            reasons.append("Unusual transaction pattern")

        if float(values[1]) > 5000:
            risk_score += 20
            reasons.append("High transaction amount")

        location = request.form.get("location")
        if location and location.lower() not in ["india", "tamil nadu"]:
            risk_score += 20
            reasons.append("Transaction from unusual location")

        trust_score = 100 - risk_score

        # Decision
        if risk_score < 30:
            level = "LOW"
            action = "Approved ✅"

        elif risk_score < 70:
            level = "MEDIUM"
            action = "OTP Required 🔐"

            otp = random.randint(1000, 9999)
            otp_storage['otp'] = otp
            return render_template("otp.html", message=f"OTP: {otp}")

        else:
            level = "HIGH"
            action = "Blocked ❌"

        transaction_history.append({
            "risk": level,
            "score": risk_score,
            "trust": trust_score,
            "action": action
        })

        return render_template("dashboard.html",
                               result=level,
                               score=risk_score,
                               trust=trust_score,
                               action=action,
                               reasons=reasons)

    except:
        return "Error in input"


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    if int(request.form['otp']) == otp_storage.get('otp'):
        return render_template("dashboard.html",
                               result="MEDIUM",
                               score=50,
                               trust=50,
                               action="Approved after OTP ✅",
                               reasons=["OTP verified"])
    else:
        return "❌ Wrong OTP"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)