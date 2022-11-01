import re


class ProcessText():
    """
      [This class provides functions to extract and validate sub string from a text]
    """

    def reduce_lengthening(self, word: str):
        """Find and remove the overage of letter that follows more than twice than

          Args:
              word (str): any word

          Returns:
              str: word without letter that follows more than twice
        """
        return re.sub(r'([a-z])\1{2,}', r'\1\1', word)

    def get_urls(self, text: str):
        """Extract urls from a text

        Args:
            text (str): any text

        Returns:
            [list]: extracted urls
        """
        return re.findall("http[s]?[^\s]+", text)
        # return re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",text)

    def get_emails(self, text: str):
        """Extract emails from a text

        Args:
            text (str): any text

        Returns:
            [list]: extracted urls
        """
        return re.findall("\S*@\S*\s?", text)

    def get_numbers(self, text: str):
        """Extract any number from a text

        Args:
            text (str): any text

        Returns:
            [list]: extracted numbers
        """
        return re.findall("([\S]*[0-9]+[.,\s]?)+", text)

    def get_phone_numbers(self, text: str):
        """Extract phone numbers from a text

        Args:
            text (str): any text

        Returns:
            [list]: extracted phone numbers
        """
        return re.findall("([+]?(\([0-9]+\)[\s]?|[1-9]{2,3}[\s]?)([0-9]{3}[\s]){3,})+", text)

    def can_be_url(self, word: str):
        """check if a word can be an url

        Args:
            word (str): any word

        Returns:
            [bool]: True if the word can be url otherwise False
        """
        return re.fullmatch("([\s]?(http|\S+[.]\S+)\S*\s?)+[\s]?",  word) != None

    def can_be_email(self, word: str):
        """check if a word can be an url

        Args:
            word (str): any word

        Returns:
            [bool]: True if the word can be url otherwise False
        """
        return re.fullmatch("\S*@\S*\s?", word) != None

    def extract_short_form(self, sentence: str):
        """Extract short form from a sentence like I'am or I'll

        Args:
            sentence (str): any sentence

        Returns:
            [list]: short from
        """
        return re.findall(r"([\'][a-zA-Z]+)+|([a-zA-Z]+[\']([a-zA-Z]*[\']?)*)", sentence)

    def can_be_exclude(self, word: str):
        """Potential abreviation or compagny name

        Args:
            word (str): word

        Returns:
            bool: False if it do not match otherwise True
        """
        return re.fullmatch(r"[A-Z]{2,}|([A-Z]+[a-z]*[A-Z]+[a-z]*)+|([\.\,]?[A-Z]+[a-zA-Z]*[&-][a-zA-Z]+[\.\,]?)|([a-z]+[.]?[A-Z]+[a-zA-Z]*)+", word) != None

    def clean_text(self, sentence: str):
        return re.sub(r'([\s])\1{1,}', r'\1', self.remove_special_char(self.extract_only_text(sentence)))

    def extract_only_text(self, text):
        """ Keep only words and special characters from a text and

        Args:
            text (str): any text 

        Returns:
            str: filtered text
        """
        text = re.sub('\S*@\S*\s?', '', text)
        text = re.sub('\S*www\S*\s?', '', text)
        text = re.sub('\S*http\S*\s?', '', text)
        text = re.sub('\S*[.][a-zA-Z]{2,4}', '', text)
        return re.sub('\S*[0-9]\S*\s?', '', text)

    def remove_special_char(self, text: str):
        """Extract special characters from a text and keep only ' and ’ and “” 

        Args:
            text (str): any text

        Returns:
            str: filtered text
        """
        return re.sub(r"[^a-zA-Z0-9-“”\s\'\n]", "", text)

    def word_special_char_at(self, word: str):
        """Check the index of a special characters in a word

        Args:
            word (str): any word

        Returns:
            bool|int: False if it do not special characters otherwise the index of the special characters
        """
        regex = re.compile('[!&*()<>?/\|}{~:,;”“]')
        res = regex.search(word)
        return False if res is None else word[res.span()[0]]

    def is_phone_number(self, word: str):
        """Check if a word is a phone number

        Args:
            word (str): any word

        Returns:
            bool: True if is a phone number otherwise False
        """
        return re.fullmatch("[+]?(\([0-9]+\)?|[0-9]+)[\s]?(([0-9]{2,3})[\s]?){3,}", word) != None

    def contains_number(self, word: str):
        """Check if a word contains number

        Args:
            word (str): any word

        Returns:
            bool: True if contains number otherwise False
        """
        return re.fullmatch("[^\s]?([0-9]+[.,\s]?)+[^\s]?",  word) != None
