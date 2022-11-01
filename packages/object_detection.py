import tensorflow as tf
import numpy as np
from numpy import expand_dims
from tensorflow.keras.models import load_model

import tensorflow_hub as hub
import PIL
from tensorflow.keras.models import model_from_json


from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array

import tempfile
from six.moves.urllib.request import urlopen
from six import BytesIO

from PIL import Image
from PIL import ImageOps

import time

import os

CHART_DET_MODEL = os.environ.get("CHART_DET_MODEL")
CHART_DET_WEIGHTS = os.environ.get("CHART_DET_WEIGHTS")
OBJECT_DET_MODEL = os.environ.get("OBJECT_DET_MODEL")


def load_TF_model():
    #module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"

    return hub.load(OBJECT_DET_MODEL).signatures['default']


class ObjectDetectionTF():

    def __init__(self, vgg_model, confidence=0.1):
        self.model = vgg_model
        self.confidence = confidence

    def get_objects(self, image_arr):

        converted_img = tf.image.convert_image_dtype(
            image_arr, tf.float32)[tf.newaxis, ...]
        start_time = time.time()
        result = self.model(converted_img)
        end_time = time.time()

        result = {key: value.numpy() for key, value in result.items()}

        indexes = [i for i, val in enumerate(
            result["detection_scores"]) if val > self.confidence]

        return " ".join([result["detection_class_entities"][i].decode("utf-8") for i in indexes])


def load_yolo_model(path="model.h5"):
    return load_model(path)


class ObjectDetectionYOLO():
    labels = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck",
              "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
              "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
              "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
              "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
              "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
              "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
              "chair", "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
              "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
              "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]

    def __init__(self, model_yolo):
        self.model = model_yolo

    def _sigmoid(self, x):
	    return 1. / (1. + np.exp(-x))

    def _decode_netout(self, netout, anchors, obj_thresh, net_h, net_w):
        grid_h, grid_w = netout.shape[:2]
        nb_box = 3
        netout = netout.reshape((grid_h, grid_w, nb_box, -1))
        nb_class = netout.shape[-1] - 5
        boxes = []
        netout[..., :2] = self._sigmoid(netout[..., :2])
        netout[..., 4:] = self._sigmoid(netout[..., 4:])
        netout[..., 5:] = netout[..., 4][..., np.newaxis] * netout[..., 5:]
        netout[..., 5:] *= netout[..., 5:] > obj_thresh

        for i in range(grid_h*grid_w):
            row = i / grid_w
            col = i % grid_w
            for b in range(nb_box):
                # 4th element is objectness score
                objectness = netout[int(row)][int(col)][b][4]
                if(objectness.all() <= obj_thresh):
                    continue
                # first 4 elements are x, y, w, and h
                x, y, w, h = netout[int(row)][int(col)][b][:4]
                x = (col + x) / grid_w  # center position, unit: image width
                y = (row + y) / grid_h  # center position, unit: image height
                w = anchors[2 * b + 0] * np.exp(w) / net_w  # unit: image width
                h = anchors[2 * b + 1] * \
                    np.exp(h) / net_h  # unit: image height
                # last elements are class probabilities
                classes = netout[int(row)][col][b][5:]
                box = BoundBox(x-w/2, y-h/2, x+w/2, y+h/2, objectness, classes)
                boxes.append(box)
        return boxes

    # load and prepare an image
    def _load_image_pixels(self, image_array, shape):
        height, width, ch = image_array.shape
        if ch > 3:
            image_array = image_array[:, :, :3]

        image = np.array(PIL.Image.fromarray(image_array).resize((128, 128)))
        #height, width = (128,128)
        # scale pixel values to [0, 1]
        image = image.astype('float32')
        image /= 255.0
        # add a dimension so that we have one sample
        image = np.expand_dims(image, 0)
        return image, width, height

    # get all of the results above a threshold
    def _get_labels(self, boxes, labels, thresh):
        v_labels = ""
        # enumerate all boxes
        for box in boxes:
            # enumerate all possible labels
            for i in range(len(labels)):
                # check if the threshold for this label is high enough
                if box.classes[i] > thresh:
                    v_labels += (labels[i]) + " "
                    # don't break, many labels may trigger for one box
        return v_labels

    def get_objects(self, image_array):
        #extract objects from image

        # define the expected input shape for the model
        input_w, input_h = 416, 416

        image, image_w, image_h = self._load_image_pixels(
            image_array, (input_w, input_h))

        # make prediction
        try:
            yhat = self.model.predict(image)
        except Exception as e:
            print(e)
            return ""

        # define the anchors
        anchors = [[116, 90, 156, 198, 373, 326], [
            30, 61, 62, 45, 59, 119], [10, 13, 16, 30, 33, 23]]
        # define the probability threshold for detected objects
        class_threshold = 0.6
        boxes = list()
        for i in range(len(yhat)):
            # decode the output of the network
            boxes += self._decode_netout(yhat[i][0],
                                         anchors[i], class_threshold, input_h, input_w)

        return self._get_labels(boxes, self.labels, class_threshold)


class BoundBox:
	def __init__(self, xmin, ymin, xmax, ymax, objness=None, classes=None):
		self.xmin = xmin
		self.ymin = ymin
		self.xmax = xmax
		self.ymax = ymax
		self.objness = objness
		self.classes = classes
		self.label = -1
		self.score = -1

	def get_label(self):
		if self.label == -1:
			self.label = np.argmax(self.classes)

		return self.label

	def get_score(self):
		if self.score == -1:
			self.score = self.classes[self.get_label()]

		return self.score


def load_chart_model(model_conf=CHART_DET_MODEL, model_weights=CHART_DET_WEIGHTS):
    json_file = open(model_conf, 'r')
    loaded_model_json = json_file.read()
    json_file.close()

    loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    loaded_model.load_weights(model_weights)

    return loaded_model


class GraphDetection():

    class_names = ['BarGraph', 'ScatterGraph', 'NetworkDiagram', 'Map', 'VennDiagram',
                   'LineGraph', 'ParetoChart', 'TreeDiagram', 'FlowChart', 'PieChart',
                   'BubbleChart', 'AreaGraph', 'BoxPlot']

    def __init__(self, chart_model, confidence=0.2):
        self.model = chart_model
        self.shape = (224, 224)
        self.confidence = confidence


    def download_and_resize_image(self, url):
        _, filename = tempfile.mkstemp(suffix=".jpg")
        response = urlopen(url)
        image_data = response.read()
        image_data = BytesIO(image_data)
        pil_image = Image.open(image_data)
        pil_image = ImageOps.fit(pil_image, self.shape, Image.ANTIALIAS)
        pil_image_rgb = pil_image.convert("RGB")
        pil_image_rgb.save(filename, format="JPEG", quality=90)
        #print("Image downloaded to %s." % filename)

        return filename

    def get_chart_type(self, image_arr=[], network_path="", local_path=""):

        if len(image_arr) == 0 and local_path == "" and network_path == "":
            return []

        if len(image_arr) != 0:
            img = image_arr
        elif local_path != "":
            img = load_img(local_path)
        else:
            filename = self.download_and_resize_image(network_path)
            img = load_img(filename).numpy()

        img = PIL.Image.fromarray(img).resize(self.shape)

        converted_img = tf.image.convert_image_dtype(
            np.array(img), tf.float32)[tf.newaxis, ...]

        preds = self.model.predict(converted_img)

        indexes = [i for i, val in enumerate(
            preds[0]) if val > self.confidence]

        return " ".join([self.class_names[i] for i in indexes])
