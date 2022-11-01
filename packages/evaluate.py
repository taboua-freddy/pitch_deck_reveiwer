from packages.checkfontform import CheckFontForm
from packages.processText import ProcessText
from packages.speller import SpellingMistakes
from packages.parsepdf import ParsePDF
from collections import Counter
import spacy
import json

import numpy as np

from wordcloud import WordCloud, STOPWORDS
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')

STOP_WORDS = set(STOPWORDS)


class EvaluatePitch():
    """This class provides methods to evaluate power point file according some rules
    """

    def __init__(self, filename, nlp, speller, excluded_words=[], threshold_repetition_paragraph=1, threshold_repetition_slide=2):
        """constructor

        Args:
            filename (str): path to the file
            nlp (spacy.Language): nlp coming from spacy
            speller (spaCyHunSpell): instance of spaCyHunSpell
            excluded_words (list, optional): words to ignore during processing. Defaults to [].
            threshold_repetition_paragraph (int, optional): thresholf to considerate word as a repetition in a paragraph. Defaults to 1.
            threshold_repetition_slide (int, optional): thresholf to considerate word as a repetition in a slide. Defaults to 1.
        """
        self._excluded_tags = ["NNP", "CC", "CD",
                               "DT", "IN", "PRP", "PRP$", "TO", "WRB"]
        self._excluded_pos = ["AUX", "PART"]
        self._word_length = 1
        self._score_structure = 100
        self._score_format = 100
        self._score_flow = 100
        self._score = 100
        self._docs = []
        self._mistakes = []
        self.filename = filename
        self._f = ParsePDF(filename)
        self.font_form = CheckFontForm(self._f)
        self.nlp = nlp
        self.text_processer = ProcessText()
        self.speller = SpellingMistakes(self.nlp, speller, excluded_words)
        self.excluded_words = excluded_words
        self._threshold_repetition_paragraph = threshold_repetition_paragraph
        self._threshold_repetition_slide = threshold_repetition_slide

    def add_excluded_words(self, excluded_words=[]):
        self._need_update = True
        self.excluded_words.extend(excluded_words)
        self.excluded_words = list(set(self.excluded_words))

    @property
    def file(self) -> ParsePDF:
        return self._f

    @property
    def docs(self) -> list:
        # if file is not parsed yet. parse it
        if len(self._docs) == 0:
            texts = self.file.text_slides()
            for i, text in enumerate(texts, 1):
                self._docs.append(self.speller.get_mistakes(text))
        return self._docs

    @property
    def mistakes(self) -> list:
        mis = []
        for i, slide in enumerate(self._get_mistakes(), 1):
            for mistake in slide.values():
                for m in mistake:
                    if m[1] not in ["UNK"]:
                        mis.append((f"slide-{i}", m[0], m[1], m[2]))

        return mis

    @property
    def unknowns(self):
        mis = []
        for i, slide in enumerate(self._get_mistakes(), 1):
            for mistake in slide.values():
                for m in mistake:
                    if m[1] in ["UNK"]:
                        mis.append((f"slide-{i}", m[0]))

        return mis

    def _get_mistakes(self):
        if len(self._mistakes) == 0:
            self._mistakes = [mistakes for _, __, mistakes in self.docs]
        return self._mistakes

    def _display_text(self, doc, options={}):
        """Disply text with SpacyDisplacy

        Args:
            doc (spacy.tokens.Doc): doc
            options (dict, optional): options. Defaults to {}.
        """
        return spacy.displacy.render(doc, style="ent", options=options)

    def _counter(self, text_clean, threshold, excluded_tags, excluded_words, excluded_pos, word_length):
        """count word occurrences

        Args:
            text_clean (str): text
            threshold (int): number of occurence to consider as a repetion
            excluded_tags (list): list of tag to exclude
            excluded_words (list): list of words to exlude
            word_length (int, optional): min length of word to consider. Defaults to 0.

        Returns:
            list: word frequencies
        """
        excl = ["“", "”", ".", "-", ]
        excl.extend(excluded_words)
        doc = self.nlp(text_clean)
        words = []
        in_quotation = False
        #n_end_quote = doc._.n_end_quote
        #n_start_quote = doc._.n_start_quote
        for token in doc:
            if token.text == "“":
                in_quotation = True
            elif token.text in ["”", "?", "!", "."]:
                in_quotation = False
            if token.tag_ not in excluded_tags and token.pos_ not in excluded_pos and token.text not in excl and len(token.text) > word_length and not self.text_processer.can_be_exclude(token.text) and not in_quotation:
                words.append(token.text)

        word_freq = Counter(words)
        return [freq for freq in word_freq.most_common() if freq[1] > threshold]

    def count_repetitif_words(self):
        """Parse file and count word occurrences

        Returns:
            tuple: (frep_in_sentences,frep_in_slides)
        """
        slides_sents = self.file.text_slides()
        frep_in_sent = {}
        frep_in_slide = {}
        for i, slide_sents in enumerate(slides_sents, 1):

            # slide_sents = slide_sents.replace("“","").replace("”","").replace(".","").replace("-","")
            # merge slide text and count word occurrences
            text_clean = self.text_processer.clean_text(
                slide_sents.replace("\n", "."))
            frep_in_slide[f"slide-{i}"] = []
            if len(text_clean) > 1:
                # self._counter(text_clean, self._threshold_repetition_slide,self._excluded_tags, self.excluded_words, self._excluded_pos, self._word_length)
                frep_in_slide[f"slide-{i}"] = []

            # count word occurrences in each sentence
            frep_in_sent[f"slide-{i}"] = []
            for sent in slide_sents.split("\n"):
                text_clean = self.text_processer.clean_text(sent)
                if len(text_clean) > 1:
                    frep_in_sent[f"slide-{i}"].extend(self._counter(text_clean, self._threshold_repetition_paragraph,
                                                      self._excluded_tags, self.excluded_words, self._excluded_pos, self._word_length))

        return frep_in_sent, frep_in_slide

    def _parse_repetition(self, title_repetition, repetitions_freq):
        # parse repetitions to display in a table
        data = {"slides": repetitions_freq.keys(), f"{title_repetition}": []}
        for values in repetitions_freq.values():
            t = ""
            for v in values:
                t += f"{v[0]} = {v[1]} ;"
            data[f"{title_repetition}"].append(t)
        return data

    def _init_collection(self, id, collection_, is_dict=False):
        collection_[id] = collection_[
            id] if id in collection_.keys() else ({} if is_dict else [])
        return collection_

    def to_JSON(self):
        '''
        {
            "data" : {
                "slide-1" : {
                "mistakes" : [
                    {
                    "word" : xxx,
                    "suggestion" : xxx,
                    "type" : xxx,
                    "sentence" : xxx
                    },
                ],
                "unknowns" : ["xxx","xxxx"],
                "repetions_sentence": {
                    "total" : xxx,
                    "words" : [{"xxx":xxx}]
                },
                }
            },
            "evaluation" : {
            "total_repetitions" : xxx,
            "total_mistakes" : xxx,
            "score" : xxx,
            "unknowns" : [],
            }
        }
        '''
        data = {"data": {}, "evaluation": {}}
        unknowns = []
        total_rep = 0
        n_font_mistakes = 0

        # repetitive word in sentence
        paragraph_rep, _ = self.count_repetitif_words()

        # font form recommandations
        font_form_check = self.font_form.parse()

        for i, values in enumerate(paragraph_rep.values(), 1):
            self._init_collection(f"Slide-{i}", data["data"], True)
            self._init_collection("unknowns", data["data"][f"Slide-{i}"])
            self._init_collection("mistakes", data["data"][f"Slide-{i}"])
            self._init_collection("font_form_data", data["data"][f"Slide-{i}"])
            if i != 1 and i != self.file.number_pages:
                data["data"][f"Slide-{i}"]["font_form_data"] = font_form_check["font_form_data"][f"Slide-{i}"]
                for key, rec in font_form_check["font_form_data"][f"Slide-{i}"].items():
                    if not rec["good"]:
                        if key == "footer number":
                            n_font_mistakes += 5
                        else:
                            n_font_mistakes += 1
            words = []
            for v in values:
                words.append({f"{v[0]}": v[1]})

            # add repetitive words and thier occurrences
            data["data"][f"Slide-{i}"]["repetions_sentence"] = {
                "total": len(words),
                "words": words
            }
            total_rep += len(words)

        # add mistake and unknown words
        mistakes = []
        for i, slide in enumerate(self._get_mistakes(), 1):
            for mistake in slide.values():
                for m in mistake:
                    if m[1] in ["UNK"]:
                        data["data"][f"Slide-{i}"]["unknowns"].append(m[0])
                        unknowns.append(m[0])
                    else:
                        data["data"][f"Slide-{i}"]["mistakes"].append(
                            {"word": m[0], "suggestion": m[2], "type": m[1]}
                        )
                        mistakes.append(f"{m[0].lower()}-{m[1]}")

        # numeber of mistakes
        n_mistakes = len(set(mistakes))

        # score
        score_structure = self._score_structure
        score_structure = score_structure - (5*n_mistakes) - (5*total_rep)
        self._score_structure = score_structure if score_structure > 0 else 0

        score_format = self._score_format
        score_format = score_format - (10*n_font_mistakes)
        self._score_format = score_format if score_format > 0 else 0

        score_flow = self._score_flow
        score_flow = score_flow - (10*len(font_form_check["misssing_titles"]))
        self._score_flow = score_flow if score_flow > 0 else 0

        self._score = np.mean(
            [self._score_structure, self._score_format, self._score_flow])

        # evalution summary
        data["evaluation"] = {
            "total_repetitions": total_rep,
            "total_mistakes": n_mistakes,
            "n_font_form": n_font_mistakes,
            "score": self._score,
            "score_structure": self._score_structure,
            "score_format": self._score_format,
            "score_flow": self._score_flow,
            "n_slide": self.file.number_pages,
            "unknowns": list(set(unknowns)),
            "misssing_titles": font_form_check["misssing_titles"]
        }

        return json.dumps(data, indent=2)

    def evaluate(self):
        """Return the score of the file according some rules

        Returns:
            int: score
        """
        # count misatkes
        n_mistakes = len(set([d[0].lower() for d in self.mistakes]))

        paragraph_rep, _ = self.count_repetitif_words()

        # count repetitions
        nb_rep_para = sum([val for val in [len(s)
                                           for s in paragraph_rep.values()] if val != 0])

        print(f"sum of repetions in paragraphs : {nb_rep_para} ")
        print(f"sum of mistakes : {n_mistakes} ")

        # score calculation
        score = self._score
        score = score - (5*n_mistakes) - (5*nb_rep_para)
        self._score = score if score > 0 else 0

        return self._score

    def word_cloud(self, n_words=15):
        text = " ".join([word_ for word_ in word_tokenize(self.file.get_text())
                        if word_ not in STOP_WORDS and len(word_) > 1])

        wordcloud = WordCloud(width=800, height=800, max_words=n_words,
                              background_color='white',
                              stopwords=STOP_WORDS,
                              min_font_size=10)

        wordcloud = wordcloud.generate(text)

        return np.array(wordcloud)
