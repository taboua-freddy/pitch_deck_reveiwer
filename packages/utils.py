
import os
from os.path import join, getsize, getctime
from os import listdir
import base64
import io
from PIL import Image


UPLOAD_FOLDER = os.environ.get("UPLOAD_PATH")

ALLOWED_EXTENSIONS = ["pdf"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def score_color(score):
    if score > 80:
        return "#2ecc71"
    elif score > 50:
        return "#f1c40f"
    elif score > 35:
        return "#e67e22"
    return "#c0392b"


def get_files():
    file_info = []
    file_names = listdir(UPLOAD_FOLDER)

    for filename in file_names:
        f_path = join(UPLOAD_FOLDER, filename)
        file_info.append((filename, getctime(f_path), getsize(f_path)))

    return file_info

def image_to_base64(image_arr):
    file_object = io.BytesIO()
    try:
        img = Image.fromarray(image_arr.astype('uint8'))
        img.save(file_object, 'PNG')
        base64img = "data:image/png;base64," + base64.b64encode(file_object.getvalue()).decode('ascii')
        return base64img
    except:
        return None