import flask
from flask import request
import os
from dotenv import load_dotenv
from bot import ObjectDetectionBot

load_dotenv()

app = flask.Flask(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_APP_URL = os.getenv('TELEGRAM_APP_URL')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
YOLO5_URL = os.getenv('YOLO5_URL')

# Ensure all environment variables are loaded
if not all([TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, YOLO5_URL]):
    raise ValueError("One or more environment variables are missing")

# Initialize the bot here
bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, YOLO5_URL)

@app.route('/', methods=['GET'])
def index():
    return 'Ok'

@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req.get('message', {}))
    return 'Ok'

if __name__ == "__main__":
    # Add debug print to check the webhook URL
    webhook_url = f'{TELEGRAM_APP_URL}/{TELEGRAM_TOKEN}/'
    print(f"Setting webhook URL: {webhook_url}")
    # Enable debug mode during development
    app.run(host='0.0.0.0', port=8443, debug=True)
