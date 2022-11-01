from packages.parsepdf import ParsePDF
from collections import Counter
import numpy as np
import re


from collections import Counter
import re


class CheckFontForm():
    """Thsi class provide fonction to give you information about good font and form of the pdf
    """

    _titles_to_include = ["problem",
                          "vision / solution",
                          "unique value proposition or product",
                          "team or shareholder structure",
                          "financial overview",
                          "milestones or roadmap or time-line",
                          "business model",
                          "market size or segmentation",
                          "competition",
                          "Ask or financing"]

    _excluded_fonts = ["Arial", "Calibri",
                       "Times New Roman", "Comic Sans", "Papyrus"]
    _accepted_fonts = ["Roboto", "Franklin Gothic", "Avenir", "or", "Lato"]

    _min_size = 14
    _max_size = 20

    _max_slides = 14

    def __init__(self, parser: ParsePDF):
        """constructor

        Args:
            parser (ParsePDF): instance of ParsePDF
        """
        self.parser = parser
        self._data = {}

    def parse(self):
        if len(self._data) == 0:
            self._data = self._font_form_info()
        return self._data

    def s_should_add(self,text,alt=""):
        return f"No should add a {text} " if alt=="" else alt

    def _font_form_info(self):
        """Thsi function give you the summary about the font and the form of the pdf

        Returns:
            dict: missing titles and data about font and form
        """
        data = {}
        headers = []
        footers = []
        bodies = []
        footers_position = []
        footer_numbers = []
        titles = []
        #extract informations such as footers,headers,page number, titles in one loop
        for (headers_, body) in zip(self.parser.content["headers"][1:-1], self.parser.content["bodies"][1:-1]):
            headers.append(headers_["header"])
            footers.append(headers_["footer"])
            bodies.append(body)
            footer_numbers.append(headers_["footer"]["text"].replace("\n", ""))
            if headers_["footer"]["exist"]:
                footers_position.append([headers_["footer"]["position"][0], headers_["footer"]["position"][1]])
            if headers_["header"]["exist"]:
                titles.append(headers_["header"]["text"].replace("\n", ""))

        #get most used value value for each attribute across the pdf
        most_used_header_color = self._most_val_used(headers, "colors")
        most_used_header_font = self._most_val_used(headers, "fonts")

        most_used_footer_color = self._most_val_used(footers, "colors")
        most_used_footer_font = self._most_val_used(footers, "fonts")

        most_used_body_font = self._most_val_used(bodies, "fonts")
        most_used_body_color = self._most_val_used(bodies, "colors")

        #get the standard position of page number across the pdf
        footer_standard_position = np.median(footers_position, axis=0)

        #check if there are recommended titles
        is_missing_titles = [True for t in self._titles_to_include]

        for title in titles:
            for w in title.split():
                for i, t in enumerate(self._titles_to_include):
                    val = "|".join([w for w in t.split() if len(w) > 2])
                    if re.match(f"(.)*{val}(.)*", w.lower().replace("\n", "")) != None:
                        is_missing_titles[i] = False
                        break

        missing_titles = [" ".join([w.capitalize() for w in self._titles_to_include[i].split(
        )]) for i, is_missing in enumerate(is_missing_titles) if is_missing]

        for i, (headers, body) in enumerate(zip(self.parser.content["headers"][1:-1], self.parser.content["bodies"][1:-1]), 2):
            data[f"Slide-{i}"] = {}

            # header
            data[f"Slide-{i}"]["header exists"] = {"good":headers["header"]["exist"],"text":self.s_should_add("header") if  not headers["header"]["exist"] else "Yes"}
            if headers["header"]["exist"]:
                # header size
                data[f"Slide-{i}"] = self._check_size(data[f"Slide-{i}"],
                                                      headers["header"], "header", self._min_size, None)

                # header color
                data[f"Slide-{i}"] = self._check_attr(data[f"Slide-{i}"], headers["header"],
                                                      "header", "colors", most_used_header_color)
                # header font
                data[f"Slide-{i}"] = self._check_attr(data[f"Slide-{i}"],
                                                      headers["header"], "header", "fonts", most_used_header_font)

            # footer
            text = {"good":False,"text":f"Lack of page number should be {i-1} "}
            data[f"Slide-{i}"]["footer exists"] = {"good":headers["footer"]["exist"],"text":self.s_should_add("footer") if  not headers["footer"]["exist"] else "Yes"}
            if headers["footer"]["exist"]:
                # footer size
                data[f"Slide-{i}"] = self._check_size(data[f"Slide-{i}"],
                                                      headers["footer"], "footer", self._min_size, self._max_size)
                # footer color
                data[f"Slide-{i}"] = self._check_attr(data[f"Slide-{i}"], headers["footer"],
                                                      "footer", "colors", most_used_footer_color)
                # footer font
                data[f"Slide-{i}"] = self._check_attr(data[f"Slide-{i}"],
                                                      headers["footer"], "footer", "fonts", most_used_footer_font)
                # footer numerotation
                if int(footer_numbers[i-2]) == i-1:
                    text = {"good":True,"text":"Good numerotation"}
                else:
                    text = {"good":False,"text":f"Bad numerotation should be {i-1} "}
                if i-2 > self._max_slides:
                    data[f"Slide-{i}"]["max number of recommended slides"] = {"good":False,"text":f"Too much slides should be at most {self._max_slides} slides"}
                # footer position
                if footer_standard_position[0]-5 < headers["footer"]["position"][0] < footer_standard_position[0]+5 and footer_standard_position[1]-5 < headers["footer"]["position"][1] < footer_standard_position[1]+5:
                    data[f"Slide-{i}"]["footer position"] = {"good":True,"text":f"Page number at the right position"}
                else:
                    data[f"Slide-{i}"]["footer position"] = {"good":False,"text":f"Page number is not in the same position as the others"}

            if headers["footer"]["logo_exits"]:
                data[f"Slide-{i}"]["footer logo"] = {"good":True,"text":f"The Company logo is present in the footer"}
                data[f"Slide-{i}"]["footer exists"] = {"good":True,"text":"Yes"}
            else:
                data[f"Slide-{i}"]["footer logo"] = {"good":False,"text":f"Should add the Company logo in the footer"}

            if len(headers["footer"]["content"]) > 0:
                data[f"Slide-{i}"]["footer Copyright"] = {"good":True,"text":f"Copyright is not present in the footer"}
                data[f"Slide-{i}"]["footer exists"] = {"good":True,"text":"Yes"}

            data[f"Slide-{i}"]["footer number"] = text

            # body
            body_exist = len(body["sizes"]) != 0
            data[f"Slide-{i}"]["body exists"] = {"good":body_exist,"text":self.s_should_add("body") if  not body_exist else "Yes"}
            if body_exist:
                # body size
                data[f"Slide-{i}"] = self._check_size(data[f"Slide-{i}"],
                                                      body, "body", self._min_size, self._max_size)
                # body font
                data[f"Slide-{i}"] = self._check_attr(data[f"Slide-{i}"],
                                                      body, "body", "fonts", most_used_body_font)
                # body color
                text = {"good":True,"text":"Your body color matches with the other slides"}
                # if more than 2 colors
                # print(body["colors"])
                if len(body["colors"]) > 2:
                    text = {"good":False,"text":"You should use at most 2 different colors"}
                # if 2 colors
                elif len(body["colors"]) == 2:
                    # if one of the 2 colors is different to the title color
                    if most_used_header_color != None:
                        if most_used_header_color[0] not in body["colors"]:
                            text = {"good":False,"text":f"One of your body color should match with the title color "}
                # if the body color is the same as the other slildes
                elif most_used_body_color != None and most_used_body_color[0] not in body["colors"]:
                    text = {"good":False,"text":"Your body color does not match with the other slides"}

                data[f"Slide-{i}"]["body color"] = text

        return {"misssing_titles": missing_titles, "font_form_data": data}

    def _check_size(self, return_data, data, type_, min_size, max_size):
        """check if a font size is between min_size and min_size

        Args:
            return_data (dict): dictionary containning data to return
            data (dict): dictionary containning data to analyse
            type_ (string): header|body|footer
            min_size (int): min size
            max_size (int): max size

        Returns:
            dict: return_data
        """
        diff = False
        text = {"good":True,"text":"No"} 
        # check if there is differents font size detected
        n_sizes = len(data["sizes"])
        if n_sizes > 2:
            diff = True
            text =  {"good":False,"text":f"Yes {n_sizes} different fonts detected"} 
            m = np.mean(data["sizes"])
            for val in data["sizes"]:
                if m-1 < val or val > m+1:
                    diff = False
                    text = {"good":True,"text":"No"}

        return_data[f"{type_} different font size"] = text 
        # check if the size is valid
        if not diff or type_ == "body":
            size = max(data["sizes"])
            m_size_text = min(data["sizes"])
            text = {"good":True,"text":f"Your font size is {size} which is good"}

            if max_size != None and size > max_size:
                text = {"good":False,"text":f"Size {size} pt detected. Should be lower than {max_size} pt "}
            elif m_size_text < min_size:
                text = {"good":False,"text":f"Size {m_size_text} pt detected. Should be greater than {min_size} pt "}

            return_data[f"{type_} size"] = text
        return return_data

    def _check_attr(self, return_data, data, type_, attr, must_used):
        """check if an attribut has the same value in all slides

        Args:
            return_data (dict): dictionary containning data to return
            data (dict): dictionary containning data to analyse
            type_ (string): header|body|footer
            attr (string): fonts|colors
            must_used (tuple|None): attribut's value most used in other slides

        Returns:
            dict: return_data
        """
        # if many attribut's value detected
        if len(data[attr]) > 2:
            return_data[f"{type_} different {attr}"] = {"good":False,"text":f"Yes {len(data[attr])} {attr} detected"}
        else:
            text = {"good":True,"text":f"Your {attr} match with the others"}

            # compare attribut to value in other slides
            if must_used != None and must_used[0] != data[attr][0]:
                text = {"good":False,"text":f"Should be {must_used[0]}, {must_used[1]} slides use it "}

            # check if there are fonts to exclude
            if attr == "fonts":
                if data[attr][0] in self._excluded_fonts:
                    reco = " ".join(self._accepted_fonts)
                    return_data[f"{type_} {attr} type"] = {"good":False,"text":f"{data[attr][0]} detected you should use {reco} "}

            return_data[f"{type_} {attr}"] = text

        return return_data

    def _most_val_used(self, data, attr, take=1):
        """Give a specific attribut this most used value across the pdf

        Args:
            data (dict): data about header, body or footer
            attr (string): colors|fonts|sizes
            take (int, optional): number of values to return. Defaults to 1.

        Returns:
            list: [(values,occurrence)]
        """
        occurrences = []
        for d in data:
            if d["exist"]:
                occurrences.append(d[attr][0])
                continue
            occurrences.append("No detected")
        ordered = Counter(occurrences).most_common()
        #print(ordered)
        if len(ordered) == 0:
            return None
        if take == 1:
            return ordered[0]
        return ordered[0:take]
