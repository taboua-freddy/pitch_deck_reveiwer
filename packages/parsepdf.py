
from PIL import Image as PIL_Image
import PIL
import fitz
import re
from io import BytesIO
import unicodedata
import numpy as np


from PIL import Image as PIL_Image
import PIL
import fitz
import re
from io import BytesIO
import unicodedata
import numpy as np


class ParsePDF():
    """This class provides methodes to parse a power point file
    """

    def __init__(self, filename):
        """constructor

            Args:
                filename (str): path to the file
        """
        self._content = {}
        self._text_slides = []
        try:
            self._f = fitz.open(filename)
        except:
            raise FileNotFoundError(f"can't open file {filename}")

    @property
    def number_pages(self):
        return len(self._f)

    def text_slides(self):
        # Parse one time to avoid repetitif parse for each request
        if len(self._text_slides) == 0:
            self._text_slides = self._get_text_slides()

        return self._text_slides

    def _process_image(self, blob):
        """convert blob into ndarray

        Args:
            blob (blob): blob image

        Returns:
            ndarray|None: image
        """
        #return np.array(PIL_Image.open(BytesIO(blob)))
        try:
            return np.array(PIL_Image.open(BytesIO(blob)))
        except:
            print("failed to load image")
        return

    def _cal_area(self, rect):
        """extract height and width of a box an return area

        Args:
            rect (tuple): rectangle (x0,y0,x1,y1)

        Returns:
            float: area
        """
        x0 = abs(rect[0])
        x1 = abs(rect[2])
        y0 = abs(rect[1])
        y1 = abs(rect[3])
        return abs(x1-x0)*abs(y1-y0)

    def get_images_slide(self):
        """get images group by slide

        Returns:
            list: ndarray of images
        """
        return self.content["images"]

    @property
    def get_images(self):
        images = []
        for imgs in self.content["images"]:
            images.extend(imgs)
        return images

    def get_bg_images_slide(self):
        """get images group by slide

        Returns:
            list: ndarray of images
        """
        return self.content["bg"]

    def get_text_ratio(self) :
        """Return of texts area for each slide

        Returns:
            list: list of float
        """
        return self.content["ratios_text"]

    def get_image_ratio(self) :
        """Return of images area for each slide

        Returns:
            list: list of float
        """
        return self.content["ratios_image"]

    def get_ratios_texts_images(self) :
        return []

    def _get_text_slides(self, join_by=" "):
        """get text from each slide

            Args:
                join_by (str, optional): paragraph separator. Defaults to " ".

            Returns:
                list
        """
        text_slide = []
        for headers, body in zip(self.content["headers"], self.content["bodies"]):
            text_slide.append(
                headers["header"]["text"]+body["text"]+headers["footer"]["text"])

        return text_slide

    def get_text(self, join_by=".", join_sentences_by=" ") :
        """merge all the text get into the power point file

            Args:
                join_by (str, optional): slide separator. Defaults to ".".

            Returns:
                str: merged text
        """
        return re.sub(r'([\s])\1{1,}|([\.])\1{1,}', r'\1', f"{join_by}".join(self.text_slides()))

    @property
    def content(self):
        if len(self._content) == 0:
            self._content = self._parse_doc()

        return self._content

    def _parse_doc(self):
        alpha = 2
        sample = self._f[0].getText("dict")
        height_header = sample["height"]/4 #170
        height_footer = sample["height"]/6 #140
        print(height_header,height_footer)

        all_header_footer = []
        all_body = []
        ratios_image = []
        ratios_text = []
        text_slide = []
        images_slide = []
        images_bg_slide = []
        logo = {"images":[],"exist":False}
        for j,page in enumerate(self._f,1):
            dic_ = page.getText("dict")
            width = dic_["width"]
            height = dic_["height"]
            slide_area = width*height
            blocks = dic_["blocks"]
            slide_images = []
            slide_bg_images = []
            images_area = 0
            texts_area = 0
            prev_block = 0
            limit_header = height_header
            limit_footer = height - height_footer
            text = ""
            num_header = -1
            num_footer = {"block_number":-1,"span_index":-1 }
            sorted_blocks = (sorted(blocks,key = lambda b : b["bbox"][1]))
            header_size = 0

            #find the header
            for i,b in enumerate(sorted_blocks):
                if b["type"]==0:
                    if b["bbox"][1] > limit_header:
                        break
                    if b["bbox"][1] < limit_header:
                        if b["lines"][0]["spans"][0]["size"] > header_size:
                            num_header = b["number"]
                            header_size = b["lines"][0]["spans"][0]["size"]
                        
            #find the footer
            for b in sorted_blocks[::-1]:
                if b["type"]==0:
                    if b["bbox"][1] < limit_footer:
                        break
                    if b["bbox"][1] > limit_footer:
                        l = ""
                        for lines in b["lines"]:
                            for i,spans in enumerate(lines["spans"]):
                                l = spans["text"]
                                #print(l)
                                #check if there is a number in the footer
                                if (l).replace("\n","").isnumeric():
                                    num_footer = {"block_number":b["number"],"span_index":i }
                                    
                                    break
                        
                       
            header_footer = {
                "header":{"text":"","fonts":[],"colors":[],"sizes":[],"position":(-1,-1,-1,-1),"exist":False,"logo_exits":False,"content":""},
                "footer":{"text":"","fonts":[],"colors":[],"sizes":[],"position":(-1,-1,-1,-1),"exist":False,"logo_exits":False,"content":""}
                }
            body = {"text":"","fonts":[],"colors":[],"sizes":[],"exist":False}
            sizes = []
            fonts = [] 
            colors = []
            for i,b in enumerate(blocks):
                #images
                if b["type"]==1:
                    #exclude background image
                    if b["bbox"][0] < 2 or b["bbox"][1] < 2 or abs(b["bbox"][2])> (width-2) or abs(b["bbox"][3]) >  (height-2) :
                        slide_bg_images.append(self._process_image(b["image"]))
                        continue
                    #search for logo in the first slide
                    #print(b["bbox"],j,height)
                    if b["bbox"][1] > limit_header and  abs(b["bbox"][3]) < limit_footer and j==1:
                        logo["images"].append(self._process_image(b["image"]))
                        logo["exist"] = True
                        continue
                    #search logo in the footer
                    if abs(b["bbox"][3]) >= limit_footer:
                        header_footer["footer"]["logo_exits"] = True
                        header_footer["footer"]["logo"] = self._process_image(b["image"])
                        continue
                    #search logo in the header
                    if abs(b["bbox"][3]) <= limit_header:
                        header_footer["header"]["logo_exits"] = True
                        header_footer["header"]["logo"] = self._process_image(b["image"])
                        continue

                    images_area += self._cal_area(b["bbox"])
                    slide_images.append(self._process_image(b["image"]))
                #text
                elif b["type"]==0:
                    texts_area += self._cal_area(b["bbox"])
                    l = ""
                    
                    #for each sub block
                    for lines in b["lines"]:
                        #for each sub sub block get text
                        for span_index,spans in enumerate(lines["spans"]):
                            l += spans["text"]
                            sizes.append(int(spans["size"]))
                            fonts.append(spans["font"])
                            colors.append(hex(spans["color"]).replace("0x","#"))#
                            if b["number"] == num_footer["block_number"] and span_index == num_footer["span_index"]:
                                l = spans["text"]
                                sizes = [int(spans["size"])]
                                fonts = [spans["font"]]
                                colors = [hex(spans["color"]).replace("0x","#")]
                                header_footer["footer"]["position"] = spans["bbox"]
                                break

                        #replace \n to make a sentence and delete double space
                        l = re.sub(r'([\s])\1{1,}', r'\1', l.replace("\n"," ")+"\n")
                    # exlude sentences with copyright
                    if re.match(r"[\s]*copyright (.)* all rights reserved[\s]*|(.)*confidential(.)*",l.lower())!=None and abs(b["bbox"][3]) >= limit_footer :
                        header_footer["footer"]["content"] = unicodedata.normalize("NFKD",l)

                    if b["number"] ==  num_header:
                        header_footer["header"]["text"] = unicodedata.normalize("NFKD",l)
                        header_footer["header"]["sizes"] = list(set(sizes))
                        header_footer["header"]["fonts"] = list(set(fonts))
                        header_footer["header"]["colors"] = list(set(colors))
                        header_footer["header"]["position"] = b["bbox"]
                        header_footer["header"]["exist"] = True
                        sizes = []
                        fonts = []
                        colors = []
                    elif b["number"] ==  num_footer["block_number"]:     
                        header_footer["footer"]["text"] = unicodedata.normalize("NFKD",l) #[w for w in l.split() if w.replace("\n","").isnumeric()][0]
                        header_footer["footer"]["sizes"] = list(set(sizes))
                        header_footer["footer"]["fonts"] = list(set(fonts))
                        header_footer["footer"]["colors"] = list(set(colors))
                        header_footer["footer"]["exist"] = True
                        sizes = []
                        fonts = []
                        colors = []
                    else:
                        # calcul space between block to know if the sentence continue in this block
                        diff = abs(b["bbox"][1]-blocks[prev_block]["bbox"][-1])
                        if diff < alpha and diff > 0:
                            body["text"] = body["text"][:-1] + " " + l
                        else:
                            body["text"] += l

                        body["exist"] = True
                        body["sizes"].extend(sizes) 
                        body["fonts"].extend(fonts) 
                        body["colors"].extend(colors) 

                        prev_block=i

            body["sizes"] = list(set(body["sizes"]))
            body["fonts"] = list(set(body["fonts"])) 
            body["colors"] = list(set(body["colors"])) 

            #normalize unicode characters
            body["text"] = unicodedata.normalize("NFKD",body["text"])


            images_slide.append(slide_images)
            images_bg_slide.append(slide_bg_images)

            #image ratio calcul
            ratio_image = images_area/slide_area
            if ratio_image > 1:
                ratio_image = 1
            #text ratio calcul
            ratio_text = texts_area/slide_area
            if ratio_image > 1:
                ratio_image = 1
            #append of ratios
            ratios_image.append(ratio_image) 
            ratios_text.append(ratio_text) 

            all_header_footer.append(header_footer)
            all_body.append(body)
        return {"logo":logo,"ratios_image":ratios_image,"ratios_text":ratios_text,"bodies":all_body,"images":images_slide,"bg":images_bg_slide,"headers":all_header_footer}
