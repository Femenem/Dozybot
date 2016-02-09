import json
import logging
import os

logger = logging.getLogger("__main__")

def fileIO(filename, IO, data=None):
    if IO == "save" and data != None:
        with open(filename, encoding='utf-8', mode="w") as f:
            f.write(json.dumps(data))
    elif IO == "load" and data == None:
        with open(filename, encoding='utf-8', mode="r") as f:
            return json.loads(f.read())
    elif IO == "check" and data == None:
        try:
            with open(filename, encoding='utf-8', mode="r") as f:
                return True
        except:
            return False
    else:
        logger.info("Invalid fileIO call")
