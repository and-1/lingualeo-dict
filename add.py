#!/usr/bin/env python3
import urllib
import urllib.request as urllib2
import json
from http.cookiejar import CookieJar
import sys

class Lingualeo:
    WORDSETS_ATTRIBUTE_LIST = {"type": "type", "id": "id", "name": "name", "countWords": "cw",
                           "countWordsLearned": "cl", "wordSetId": "wordSetId", "picture": "pic",
                           "category": "cat", "status": "st", "source": "src"}

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cj = CookieJar()

    def auth(self):
        url = 'https://lingualeo.com/api/auth'
        extra_headers = {'Referer': 'https://lingualeo.com/ru/'}
        values = {
            "type": "mixed",
            "credentials": {"email": self.email, "password": self.password}
        }

        return self.get_content(url, values, extra_headers)

    def get_wordsets(self):
        err = None
        """
        Get user's dictionaries (wordsets), including default ones,
        and return ids and names of not empty ones
        """
        wordsets = []
        url = 'https://api.lingualeo.com/GetWordSets'
        values = {'apiVersion': '1.0.0',
                  'request': [{'subOp': 'myAll', 'type': 'user', 'perPage': 999,
                               'attrList': lingualeo.WORDSETS_ATTRIBUTE_LIST, 'sortBy': 'created'}],
                  'ctx': {'config': {'isCheckData': True, 'isLogging': True}}}
        try:
            response = json.loads(self.get_content(url, values))
            if response.get('error') or not response.get('data'):
                raise Exception('Incorrect data received from LinguaLeo. Possibly API was changed again. '
                                + response.get('error').get('message'))
            all_wordsets = response['data'][0]['items']
            # Add only non-empty dictionaries
            for wordset in all_wordsets:
                wordsets.append({'name': wordset['name'], 'id': wordset['id']})
            if not wordsets:
                err = 'No user dictionaries found'
        except urllib.error.URLError:
            err = "Can't get dictionaries. Problem with internet connection."
        except ValueError:
            err = "Error! Possibly, invalid data was received from LinguaLeo."
        except KeyError:
            err = f"Can't get list of wordsets. Possibly API was changed again. Please {github_message}"
        except Exception as e:
            err = f"There's been an unexpected error. Please {github_message}. Error: {str(e)}"
        if err:
            wordsets = []

        return wordsets

    def is_authorized(self):
        url = 'https://api.lingualeo.com/isauthorized'
        response = self.opener.open(url)
        status = json.loads(response.read()).get('is_authorized', False)
        return status

    def add_word(self, word, translates, dict_id):
        url = "https://api.lingualeo.com/SetWords"
        translate = translates[0]
        for tr in translates:
            if tr["votes"] > translate["votes"]:
                translate = tr.copy()
        data = {
            "data": [{
               "action": "add",
               "valueList": {
                    "langPair": {"source": "en", "target": "ru"},
                    "translation": {
                        "ctx": translate["ctx"],
                        "pic": translate["pic_url"],
                        "tr": translate["value"],
                    },
                    "wordSetId": dict_id,
                    "wordValue": word
                }
            }],
            "apiVersion": "1.0.0",
            "userId": "and-1", 
        }
        self.get_content(url, data)

    def get_translates(self, word):
        url = "https://api.lingualeo.com/gettranslates"

        data = { 
                "data": {
                    "text": word, 
                    "langPair": {
                        "source": "en", 
                        "target": "ru"
                    }
                },
                "apiVersion": "1.0.0"
        }   

        try:
            result = self.get_content(url, data)
            return json.loads(result)["translate"]
        except Exception as e:
            return e.message

    def get_content(self, url, values, more_headers=None):
        data = json.dumps(values).encode("utf-8")

        headers = {'Content-Type': 'application/json'}
        if more_headers:
            headers.update(more_headers)
        
        req = urllib.request.Request(url, data, headers)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        req = opener.open(req)

        return req.read()

class Word:
    text = '';
    context = '';

    def __init__(self, text):
        self.text = text

class Base(object):
    data = []

    def __init__(self, source):
        self.source = source

    def get(self):
        return self.data

    def read(self):
        raise NotImplementedError('Not implemented yet')

    def source(self):
        return self.source

class Text(Base):
    def read(self):
        f = open(self.source)
        for word in f.readlines():
            self.data.append(Word(word))
        f.close()

email = sys.argv[1]
password = sys.argv[2]

word_handler = Text(sys.argv[3])

word_handler.read()

lingualeo = Lingualeo(email, password)
lingualeo.auth()
print("ID\tNAME")
for i in lingualeo.get_wordsets():
    print(f"{i['id']}\t{i['name']}")

dict_id = input('Select id of dictionary.\n')

for word_dto in word_handler.get():
    word = word_dto.text.lower()
    translates = lingualeo.get_translates(word)
    
    if len(translates) == 0:
        print(f"Translation not found for word {word}")
        continue

    if translates[0]["is_user"]:
        print(f"Already exists: {word.strip()}")
    else:
        print(f"Adding word: {word.strip()} to dict {dict_id}...")
        lingualeo.add_word(word, translates, dict_id)
