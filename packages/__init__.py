__all__ = ['ParsePDF', 'SpellingMistakes',
           'ProcessText', 'GingerIt', 'CheckWordOnline', 'EvaluatePitch', 
           'CheckFontForm', "load_TF_model", "ImagesProcessing", "load_chart_model", 
           "GraphDetection", "ObjectDetectionTF","allowed_file","score_color","get_files"]

from .parsepdf import ParsePDF
from .speller import SpellingMistakes
from .processText import ProcessText
from .gingerIt import GingerIt, CheckWordOnline
from .evaluate import EvaluatePitch
from .checkfontform import CheckFontForm
from .image_processing import ImagesProcessing
from .object_detection import load_TF_model, load_chart_model, GraphDetection, ObjectDetectionTF
from .utils import *
