import os
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request, redirect, Response

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load Twilio config
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL")

# Create Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH)

# Define the list of questions (scalable)
questions = [
    "Please say your full name after the beep.",
    "Please say your full address after the beep."
]

@app.route("/health", methods=["GET"])
def health_check():
    print("Health check endpoint accessed")
    return {"status": "healthy"}, 200


@app.route("/start-call", methods=["POST"])
def start_call():
    step = 0
    return redirect(f"/ask?step={step}")

@app.route("/ask", methods=["GET", "POST"])
def ask():
    step = int(request.args.get("step", 0))
    prev_recordings = request.args.get("recordings", "")

    if step >= len(questions):
        return redirect(f"/final-webhook?recordings={prev_recordings}")

    question = questions[step]
    return Response(f"""
    <Response>
        <Say voice=\"alice\">{question}</Say>
        <Record 
            action=\"/handle-answer?step={step}&recordings={prev_recordings}\" 
            method=\"POST\"
            maxLength=\"15\" 
            finishOnKey=\"*\" 
            playBeep=\"true\" />
    </Response>
    """, mimetype='text/xml')

@app.route("/handle-answer", methods=["POST"])
def handle_answer():
    step = int(request.args.get("step", 0))
    prev_recordings = request.args.get("recordings", "")
    recording_url = request.form.get("RecordingUrl")

    updated_recordings = f"{prev_recordings},{recording_url}" if prev_recordings else recording_url
    next_step = step + 1
    return redirect(f"/ask?step={next_step}&recordings={updated_recordings}")

@app.route("/final-webhook", methods=["GET", "POST"])
def final_webhook():
    recordings = request.args.get("recordings", "")
    recording_urls = recordings.split(",")

    results = []
    for i, url in enumerate(recording_urls):
        results.append(f"Q{i+1}: {questions[i]}")
        results.append(f"Recording: {url}.wav")

    return "\n".join(results)

@app.route("/initiate-call", methods=["POST"])
def initiate_call():
    to_number = request.form.get("to")
    if not to_number:
        return "Missing 'to' phone number", 400

    call = client.calls.create(
        twiml=f"""
        <Response>
            <Say voice=\"alice\">Hi, I’m Dorothy from XYZ wealth management.</Say>
            <Redirect method=\"POST\">{BASE_URL}/start-call</Redirect>
        </Response>
        """,
        to=to_number,
        from_=TWILIO_PHONE_NUMBER
    )

    return f"Call initiated: {call.sid}"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
