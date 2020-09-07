from flask import Flask, request
from PIL import Image

from app.detection import detect_read
from app.parse_info import parse

app = Flask(__name__)

@app.route('/detect', methods=['GET','POST'])
def detect():
    if 'image' in request.files:
        image = Image.open(request.files['image']).convert('RGB')
        return detect_read(image)