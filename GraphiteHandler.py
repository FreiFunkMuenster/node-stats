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


import socket
import datetime
import re


class GraphiteHandler(object):

    def __init__(self, server, port, alternative_now = None):
        self.server = server
        self.port = port
        self.entries = []
        self.specialChars = dict.fromkeys(map(ord, ' +.\\/-'), '_')

        if alternative_now:
            self.utc_stamp_now = datetime.datetime.strptime(alternative_now, '%Y-%m-%d_%H-%M-%S').strftime("%s")
        else:
            self.utc_stamp_now = datetime.datetime.now().strftime("%s")

    @property
    def message(self):
        return ''.join(self.entries)

    def prepareMessage(self, domains, nodes):
        self.__nestedWalker__('nodes', domains)
        self.__nestedWalker__('node', nodes)
        # print(self.message)
        # self.send(self.message)

    def __nestedWalker__(self, prefix, tree):
        if isinstance(tree, dict):
            for k, v in tree.items():
                if k:
                    self.__nestedWalker__(''.join((prefix, '.', k.translate(self.specialChars))), v)
        elif isinstance(tree, bool):
            self.entries.append(''.join((prefix, ' ', str(int(tree)), ' ', self.utc_stamp_now , '\n')))
        else:
            # credits to https://wiki.python.org/moin/PythonSpeed/PerformanceTips#String_Concatenation
            self.entries.append(''.join((prefix, ' ', str(tree), ' ', self.utc_stamp_now , '\n')))

    def filterMessage(self, pattern, fMode = 'normal', fType = 'graphite_filter'):
        if fType == 'graphite_filter':
            self.__graphiteFilter__(pattern, fMode)
        else:
            raise Exception('Selected filter type is not implemented, yet.')


    def __graphiteFilter__(self, pattern, fMode):
        inverse = True if fMode == 'inverse' else False
        regex = re.compile(pattern)
        filteredEntries = []
        for entry in self.entries:
            match = regex.search(entry)
            if match and not inverse or inverse and not match:
                filteredEntries.append(entry)
        self.entries = filteredEntries

    def printMessage(self):
        print(self.message)

    def sendMessage(self):
        sock = socket.socket()
        sock.connect((self.server, int(self.port)))
        sock.sendall(self.message.encode())
        sock.close()
