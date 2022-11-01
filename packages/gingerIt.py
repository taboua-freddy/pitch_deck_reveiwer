
import requests

URL = "https://services.gingersoftware.com/Ginger/correct/jsonSecured/GingerTheTextFull"  # noqa
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"


class GingerIt(object):
    '''API to analyse sentence context to find mistakes

    '''

    def __init__(self):
        self.url = URL
        self.api_key = API_KEY
        self.api_version = "3.0"
        self.lang = ["US", "UK"]

    def parse(self, text, verify=True):
        session = requests.Session()
        request = session.get(
            self.url,
            params={
                "lang": self.lang,
                "apiKey": self.api_key,
                "clientVersion": self.api_version,
                "text": text,
            },
            verify=verify,
        )
        data = request.json()
        return self._process_data(text, data)

    @staticmethod
    def _change_char(original_text, from_position, to_position, change_with):
        return "{}{}{}".format(
            original_text[:from_position], change_with, original_text[to_position + 1:]
        )

    def _process_data(self, text, data):
        result = text
        corrections = []

        for suggestion in reversed(data["Corrections"]):
            start = suggestion["From"]
            end = suggestion["To"]

            if suggestion["Suggestions"]:
                suggest = suggestion["Suggestions"][0]
                result = self._change_char(result, start, end, suggest["Text"])

                corrections.append(
                    {
                        "start": start,
                        "text": text[start: end + 1],
                        "correct": suggest.get("Text", None),
                        "definition": suggest.get("Definition", None),
                    }
                )

        return {"text": text, "result": result, "corrections": corrections}


class CheckWordOnline():

    def __init__(self):
        self._url = "https://www.merriam-webster.com/dictionary/"

    def word_exist(self, text):
        try:
            session = requests.Session()
            request = session.get(self._url+text)
        except:
            return False
        return (request.status_code != 404)
