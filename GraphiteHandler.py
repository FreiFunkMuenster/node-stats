#!/usr/bin/env python3
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


import socket, time

class GraphiteHandler(object):
    def __init__(self,server,port):
        self.server = server
        self.port = port
        self.message = ''
        self.entries = []
        self.specialChars = dict.fromkeys(map(ord, ' +.\\/-'), '_')

    def prepareMessage(self, domains, nodes):
        self.__nestedWalker__('nodes',domains)
        self.__nestedWalker__('node',nodes)
        self.message = self.message.join(self.entries)
        print(self.message)

    def __nestedWalker__(self, prefix, tree):
        if isinstance(tree, dict):
            for k, v in tree.items():
                self.__nestedWalker__(''.join((prefix, '.', k.translate(self.specialChars))),v)
        else:
            # credits to https://wiki.python.org/moin/PythonSpeed/PerformanceTips#String_Concatenation
            self.entries.append(''.join((prefix, ' ', str(tree), '\n')))
