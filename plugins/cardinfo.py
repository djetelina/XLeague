#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

import json
import re

from twisted.internet.defer import inlineCallbacks
from twisted.web.client import getPage

url_base = "http://api.deckbrew.com/mtg/cards/"


@inlineCallbacks
def fetch(name):
    """
    Get information about card

    :param name:        Card to look up
    :return:            Generator for string with card information (2 lines)
                            use yield to retrieve the information
    """
    apiurl = url_base + re.sub("[\'\",]", "", re.sub(" ", "-", name.lower()))
    data = yield getPage(apiurl)
    reply = cardprocess(data)
    yield reply


def cardprocess(data):
    data = json.loads(data)
    name = data["name"]
    if "supertypes" in data:
        supertypes = " ".join(data["supertypes"]) + " - "
    else:
        supertypes = ""
    types = " ".join(data["types"])
    if "subtypes" in data:
        subtypes = " - " + " ".join(data["subtypes"])
    else:
        subtypes = ""
    if len(data["cost"]) > 0:
        cost = "(" + stripcurlybraces(data["cost"]) + ") "
    else:
        cost = ""
    text = re.sub("\n", " ", stripcurlybraces(data["text"]))
    if "power" in data:
        power = " [" + data["power"] + "/" + data["toughness"] + "]"
    else:
        power = ""
    reply = "{} [{}{}{}] {}\n{}{}".format(name, supertypes, types, subtypes,
                                          cost, text, power)
    return reply


def stripcurlybraces(s):
    return re.sub("[{}]", "", s)
