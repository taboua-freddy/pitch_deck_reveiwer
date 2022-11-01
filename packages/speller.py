import contractions
from spacy.tokens import Span
from spellchecker import SpellChecker
import spacy
from .gingerIt import GingerIt, CheckWordOnline
from .processText import ProcessText


class SpellingMistakes():

    _contraction_suffixes = []

    def __init__(self, nlp: spacy.Language, speller, excluded_words=[]):
        """constructor

        Args:
            nlp (spacy.Language): nlp coming from spacy
            speller (hunspell.HunSpell): instance of hunspell.HunSpell
            excluded_words (list, optional): words to ignore during processing. Defaults to [].
        """

        self.nlp = nlp
        self.speller1 = SpellChecker("en")
        self.speller = speller
        self.grammar_parser = GingerIt()
        self.excluded_words = excluded_words
        self._need_update = False
        self.online_checker = CheckWordOnline()
        self.text_processer = ProcessText()
        #self.speller = spaCyHunSpell(nlp, 'linux')

    def add_excluded_words(self, excluded_words=[]):
        self._need_update = True
        self.excluded_words.extend(excluded_words)
        self.excluded_words = list(set(self.excluded_words))

    @property
    def contraction_suffixes(self):
        """return suffixes of all contraction forms

        Returns:
            list: suffixes
        """
        if len(self._contraction_suffixes) == 0:
            self._contraction_suffixes = self._contraction_suffixes_init()
        return self._contraction_suffixes

    def is_grammar_known(self, tok, default_speller=True):
        """check if a token is present in the dictionary and return suggestion 

        Args:
            tok (spacy.tokens.Token): [description]
            default_speller (bool, optional): choice of the dictionary. Defaults to True.

        Returns:
            [tuple]: (is_known,suggestion)
        """
        if default_speller:
            is_known = self.speller.spell(tok.text)
            sug = [""]
            if not is_known:
                sug = self.speller.suggest(tok.text)
                if len(sug) == 0:
                    sug = [""]

            return ((is_known or sug[0] == tok.text), sug)

        sug = self.speller1.candidates(tok.text)
        return (self.speller1.correction(tok.text) == tok.text.lower(), sug if len(sug) > 0 else [""])

    def _contraction_suffixes_init(self):
        """lazy methode to extract suffixes for short forms

        Returns:
            list: suffixes
        """
        suffixes = []
        for con in contractions.contractions_dict.keys():
            doc = self.nlp(con)
            n = len(doc)
            if n == 0 or doc[0].tag_ in ["NNS", "ADD", ".", "NFP", "NNP", "UH", "NN", "FW", "VB", "JJ", "UH", "CD", "FW", "XX", "VBG"]:
                suffixes.append(doc[0].text)
            else:
                for tok in doc[1:]:
                    suffixes.append(tok.text)

        # unique suffixes
        suffixes = list(set(suffixes))
        # add some suffixes
        suffixes.extend(["will’ve", "amn't", 'sha’n’t', 'wanna', "finna", "e'er", "y'all've",
                        "'o’er'", "I'm'a", "y'", "y’", "em", 'gon’t', "gon't", "'cause", 'kinda', 'ne’er'])
        # extract suffixes which are like words
        if "all" in suffixes:
            suffixes.remove("all")
            suffixes.remove("somebody")
            suffixes.remove("someone")
            suffixes.remove("something")
            suffixes.remove("everyone")
            suffixes.remove("o")
            suffixes.remove("let")
            suffixes.remove("dare")

        return suffixes

    def _init_m(self, id, mistake_dict):
        mistake_dict[id] = mistake_dict[id] if id in mistake_dict.keys() else [
        ]
        return mistake_dict

    def get_mistakes(self, text):
        """Parse the text to find spelling mistakes

        Args:
            text (str): text

        Returns:
            tuple: (doc,colors,mistakes)

        """
        try:
            response = self.grammar_parser.parse(text)
            if "corrections" in response.keys():
                res = response["corrections"]
            else:
                res = {}
        except:
            res = {}

        grammar_mistakes = {}
        for r in res:
            grammar_mistakes[r["text"]] = (r["correct"], r["start"])

        mistakes = {}
        colors = {}
        doc = self.nlp(text)
        i = 0
        in_quotation = False

        for tok in doc:
            is_short_form = False
            # if it's a word and not in excluded_words except “ ” and ’
            if (len(self.text_processer.clean_text(tok.text)) > 0) and tok.text not in self.excluded_words and tok.text not in ["\n", "\n\n", "\n \n", "\n ", " "]:

                id = tok.i
                capitalize_next = False
                is_grammar_mistake = False

                # check capital letter in quote “”
                if tok.text in ["“"]:
                    in_quotation = True
                    # if the first letter is lower, check if it's a part of sentence or a full sentence
                    if (id+1) < len(doc) and doc[id+1].text[0].islower():
                        capitalize_next = True
                        for t in doc[id+1:]:
                            # if it's a part of sentence stop
                            if t.text in ["”"]:
                                break
                            # if it's a full sentence count as a mistake
                            elif t.text in ["?", "!", "."]:
                                mistakes = self._init_m(id+1, mistakes)
                                mistakes[id+1].append((doc[id+1].text,
                                                      "CAPI", doc[id+1].text.capitalize()))
                                break

                if tok.text in ["”", "?", "!", "."]:
                    in_quotation = False

                # exclud checking in quotation
                if not in_quotation:

                    # check capital letter
                    # or tok.tag_ in ["NNP"]
                    if (tok.is_sent_start) and (True if id == 0 else (True if doc[id-1].text in ["\n", "."] else False)) and tok.text[0].islower() and tok.text not in ["“", "”"]:
                        mistakes = self._init_m(id, mistakes)
                        mistakes[id].append(
                            (tok.text, "CAPI", tok.text.capitalize()))

                    # ckech contractions
                    if tok.text.lower() in self.contraction_suffixes:
                        is_short_form = True
                        # exclude possession like Freddy's bag
                        if doc[id-1].pos_ not in ["NOUN", "PROPN"]:

                            mistakes = self._init_m(id, mistakes)
                            # Month contraction
                            if tok.text[0].isupper() and len(tok.text) < 4:
                                mistakes[id].append(
                                    ((tok.text), "SF", contractions.fix(tok.text + ".").capitalize()))
                            else:
                                # Others contractions
                                suggestion = contractions.fix(
                                    doc[id-1].text+tok.text)
                                mistakes[id].append(((doc[id-1].text+tok.text), "SF",
                                                    suggestion.capitalize() if doc[id-1].is_sent_start else suggestion))

                    # first grammar check with gingerit model
                    if tok.text in grammar_mistakes.keys() and not is_short_form and not self.text_processer.can_be_exclude(tok.text):
                        suggestion, start = grammar_mistakes[tok.text]
                        # exclude capital letter checking for this step
                        if i-len(tok.text) < start and start < i+len(tok.text) and suggestion.lower() != tok.text.lower():
                            mistakes = self._init_m(id, mistakes)
                            # if out of vocabulary put in unknown
                            if tok.is_oov:
                                mistakes[id].append((tok.text, "UNK", ""))
                            else:
                                # otherwise it's a mistake
                                mistakes[id].append(
                                    (tok.text, "GRM", suggestion))
                            is_grammar_mistake = True
                    # if tok.is_oov:
                        # print(tok.text,tok.pos_,tok.tag_)

                    # second grammar check with spaCyHunSpell (word by word checking)
                    # and
                    if tok.tag_ != "NNP" and not is_short_form and len(tok.text) > 1 and not is_grammar_mistake and tok.is_oov:
                        is_know, suggestions = self.is_grammar_known(tok)
                        if not is_know:

                            # check if it is an Abreviation or company name
                            if self.text_processer.can_be_exclude(tok.text):
                                mistakes = self._init_m(id, mistakes)
                                mistakes[id].append((tok.text, "UNK", ""))
                            elif tok.tag_ not in ["NNPS", "NNP", "NNS", "NN"]:
                                # check the word online
                                if not self.online_checker.word_exist(tok.text):
                                    mistakes = self._init_m(id, mistakes)
                                    mistakes[id].append(
                                        (tok.text, "VOC", suggestions[0]))

            i += (len(tok.text)+(0 if is_short_form else 1))

        # add span and label in the doc
        for id, mist in mistakes.items():
            label = " | ".join([m[1] for m in mist])

            mist_ent = Span(doc, id, id+1, label=label)
            doc.set_ents([mist_ent], default="unmodified")
            colors[label] = "red"
        # set color for unknown
        if "UNK" in colors.keys():
            colors["UNK"] = "yellow"

        return doc, colors, mistakes
