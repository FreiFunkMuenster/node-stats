# -*- coding: utf8 -*-

# MIT License

# Copyright (c) 2017 Simon Wüllhorst

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import sys
import urllib.request


class JsonHandler(object):
    def __init__(self, fileName):
        self.fileName = fileName
        self.printStatus = True
        self.__jsonData__ = self.__getFile__(fileName)

    @property
    def data(self):
        return self.__jsonData__

    def __getFile__(self, fileName):
        data = None
        if fileName.startswith('https://') or fileName.startswith('http://'):
            if self.printStatus:
                print('Download', fileName.rsplit('/', 1)[-1] , 'from URL:', fileName)
            resource = urllib.request.urlopen(fileName)
            try:
                data = json.loads(resource.read().decode('utf-8'))
            except:
                print('Error while parsing a json file (perhapes misformed file): ' + fileName, file=sys.stderr)
            finally:
                resource.close()
        else:
            if self.printStatus:
                print('Open', fileName.rsplit('/', 1)[-1] , 'from file:', fileName)
            with open(fileName) as data_file:
                try:
                    data = json.load(data_file)
                except:
                    print('Error while parsing a json file (perhapes misformed file): ' + fileName, file=sys.stderr)

        return data
