import os
import ast

class EasyData:
    def __init__(self, datafile):
        self._fileName = datafile
        if not os.path.exists(datafile):
            with open(datafile, 'w+') as r:
                print(r.read())
    def getAsDict(self):
        with open(self._fileName, 'r') as r:
            return dict(ast.literal_eval(r.read()))

    def updateFile(self, dict):
        with open(self._fileName, 'w') as r:
            r.write(str(dict))
