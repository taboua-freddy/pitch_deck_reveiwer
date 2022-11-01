
from os.path import join, exists

import numpy as np
from packages.image_processing import ImagesProcessing
from packages.parsepdf import ParsePDF
from packages.object_detection import load_TF_model, load_chart_model
from packages.utils import *
from packages.evaluate import EvaluatePitch
from flask import Flask, flash, request, redirect, url_for, render_template, make_response
import os
from werkzeug.utils import secure_filename
import spacy
import hunspell
import json


# "/home/freddy/Documents/donnees/Fask/static/dictionnary/en_US"
dic = os.environ.get("DIC_PATH")
# "/home/freddy/Documents/donnees/Fask/static/dictionnary/en_US"
aff = os.environ.get("AFF_PATH")

models = {"chart_detection": load_chart_model(
), "object_detection": load_TF_model()}

nlp = spacy.load("en_core_web_lg")

speller = hunspell.Hunspell(dic, aff)
app = Flask(__name__)


UPLOAD_FOLDER = os.environ.get("UPLOAD_PATH")


ALLOWED_EXTENSIONS = ["pdf"]

pdf = None


@app.route('/processImage', methods=['POST'])
def image_consistency():
    filename = request.args.get('filename', '')
    keywords = request.form.get("keywords", "")

    ip = ImagesProcessing(nlp, models)
    pdf = ParsePDF(f"{UPLOAD_FOLDER}{filename}")

    all_images = pdf.get_images_slide()
    data = ip.get_similarity(all_images, keywords)
    colors = []

    for k, v in data[0].items():
        score = round(v*100, 2)
        data[0][k] = score
        colors.append(score_color(score))

    bad_images = {}
    for slides_index, indexes_image in data[1].items():
        _images = []
        for index_image in indexes_image:
            try:
                base64img = image_to_base64(
                    all_images[slides_index][index_image])
                if base64img != None:
                    _images.append(base64img)
            except:
                pass
        bad_images[slides_index] = _images
    #ip = ImagesProcessing(nlp, models)
    #sim, bad_images_indexes = ip.get_similarity(pdf.get_images_slide())
    resp = make_response(render_template('image_consistency.html',
                         similaries=data[0], bad_images=bad_images, colors=colors, n_charts=data[2]))
    return resp


@app.route("/show/<filename>")
def show_score(filename):
    pdf = None
    data = {}

    pdf = EvaluatePitch(f"{UPLOAD_FOLDER}{filename}", nlp, speller)
    word_cloud_img = pdf.word_cloud()
    word_cloud_img = image_to_base64(word_cloud_img)

    ratios = zip(pdf.file.get_text_ratio(), pdf.file.get_image_ratio())
    ratio_text = pdf.file.get_text_ratio()
    ratio_image = pdf.file.get_image_ratio()
    text = ""  # pdf.display_spelling_mistakes(True)
    data = json.loads(pdf.to_JSON())
    #data["data"] = sorted(data["data"].items(),key=lambda item: int(item[0].split("-")[1]))
    score_names_colors = [
        {"label": "Overall", "color": score_color(
            data["evaluation"]["score"]), "score":round(data["evaluation"]["score"], 2)},
        {"label": "Format", "color": score_color(
            data["evaluation"]["score_format"]), "score":data["evaluation"]["score_format"]},
        {"label": "Structure", "color": score_color(
            data["evaluation"]["score_structure"]), "score":data["evaluation"]["score_structure"]},
        {"label": "Flow", "color": score_color(
            data["evaluation"]["score_flow"]), "score":data["evaluation"]["score_flow"]},
    ]

    return render_template('show_score.html', ratios=ratios, filename=filename, data=data, score_names_colors=score_names_colors,
                           score_color=score_color(data["evaluation"]["score"]), ratio_text=ratio_text, ratio_image=ratio_image, word_cloud_img=word_cloud_img)


@app.route('/delete/<filename>')
def delete_file(filename):
    path = join(UPLOAD_FOLDER, filename)
    if exists(path):
        os.remove(path)
    return redirect(url_for("home"))


@app.route("/evaluate/<filename>")
def evaluate(filename):
    pdf = EvaluatePitch(f"{UPLOAD_FOLDER}{filename}", nlp, speller)

    return f"{pdf.to_JSON()()}"


@app.route('/')
def home():
    return render_template('index.html', files=get_files())


@app.route('/', methods=['POST'])
def upload_image():

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(join(UPLOAD_FOLDER, filename))

        flash('Image successfully uploaded and displayed below')
        # render_template('index.html', filename=filename)
        return redirect(url_for("home"))
    else:
        flash('Allowed image type is - pdf')
        return redirect(request.url)


if __name__ == '__main__':
    app.run()
