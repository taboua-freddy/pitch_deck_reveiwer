
import numpy as np
import re
from pytesseract import pytesseract

from packages.processText import ProcessText
from packages.object_detection import ObjectDetectionTF, GraphDetection


class ImagesProcessing():

    text_processor = ProcessText()

    def __init__(self, nlp, models):
        self.nlp = nlp
        self.object_detection = ObjectDetectionTF(
            models["object_detection"], 0.5)
        self.chart_detection = GraphDetection(models["chart_detection"], 0.8)

    def get_objects(self, image_array):
        return self.object_detection.get_objects(image_array)

    def get_text(self, image_array):
        # text extraction
        return pytesseract.image_to_string(image_array)

    def _init_collection(self, id, collection_, is_dict=False):
        collection_[id] = collection_[
            id] if id in collection_.keys() else ({} if is_dict else [])
        return collection_

    def get_similarity(self, images, key_words):
        words = ""
        objects = ""
        n_charts = 0
        doc_key_words = self.nlp(key_words)
        tags = ["NNP", "CC", "CD", "DT", "IN", "PRP", "PRP$", "TO", "WRB"]
        bad_images = {}
        for slide_index, slide_image in enumerate(images, 1):
            for i, image in enumerate(slide_image):
                _, _, ch = image.shape
                if ch > 3:
                    image = image[:, :, :3]
                # get text from image
                w = self.get_text(image)+" "
                # get objects from image
                ob = self.get_objects(image)+" "
                words += w
                objects += ob

                w = self.text_processor.clean_text(
                    re.sub('\W+', ' ', (w).lower()))
                merge = ob+w
                # similarity between image and keywords
                ratio = self.nlp(merge).similarity(doc_key_words)

                if ratio < 0.3:
                    bad_images = self._init_collection(slide_index, bad_images)
                    logo = False
                    chart = False
                    # if there is company name
                    ratio_text = np.mean([1 if (t.pos_ in ["NOUN", "PROPN"] and len(
                        t) >= 2) else 0 for t in self.nlp(w)])  # ,
                    if ratio_text >= 0.5:
                        logo = True

                    charts = self.chart_detection.get_chart_type(image)
                    if charts:
                        if ratio <= 0.0:
                            chart = True
                        n_charts += 1
                        #objects += charts + " "

                    if not logo and not chart:
                        bad_images[slide_index].append(i)

        # clean extracted object and text
        objects = objects + words
        objects = self.text_processor.clean_text(
            re.sub('\W+', ' ', objects.lower())).split()

        objects = [w for w in objects if len(w) > 2 and self.nlp(
            w)[0].tag_ not in tags and w not in ["Poster"]]
        # print(objects)

        # similarity between each keyword and all images
        simi = {}
        for tok in doc_key_words:
            # (np.mean(np.array([tok.similarity(self.nlp(w)) for w in objects])))
            simi[tok] = tok.similarity(self.nlp(" ".join(objects)))

        return simi, bad_images, n_charts
