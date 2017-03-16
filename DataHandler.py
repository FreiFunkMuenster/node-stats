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

import sys, os, collections, json

class DataHandler(object):
    def __init__(self, jsonData):
        self.data = jsonData
        self.advNodeIDs =  self.__readAdvancedNodesFile__(os.path.dirname(os.path.realpath(__file__)) + '/advnodes')
        self.gatewayIDs = list()
        self.domains = collections.defaultdict(DataHandler.__domain_dict__)
        self.nodes = DataHandler.__nested_dict__()

    def convert(self):
        for nodeID, nodeData in self.data.items():

            # credits to https://stackoverflow.com/a/1285926
            # A is not a subset of B
            if not set(('nodeinfo', 'statistics', 'neighbours')) <= set(nodeData):
                # incomplete node data so goto next node
                continue
            # try:
            self.__operateNode__(nodeID, nodeData)
            # except:
            #     print('Error while operating on node ' + nodeID + ' goto next node.', file=sys.stderr)
        print(json.dumps(self.domains, sort_keys=True, indent=4))

    def __operateNode__(self, nodeID, nodeData):
        nodeInfo = nodeData['nodeinfo']
        site = nodeInfo['system']['site_code']
        self.domains[site]['nodes_count'] += 1
        if 'software' in nodeInfo:
            sw = nodeInfo['software']
            try:
                self.domains[site]['firmwarecount'][sw['firmware']['release']] += 1
            except:
                pass
            if 'autoupdater' in sw:
                if 'branch' in sw['autoupdater']:
                    self.domains[site]['branchcount'][sw['autoupdater']['branch']] += 1

                if sw['autoupdater']['enabled']:
                    self.domains[site]['autoupdate'] += 1
        try:
            self.domains[site]['hardwarecount'][nodeInfo['hardware']['model']] += 1
        except:
            pass

        if 'location' in nodeInfo:
            self.domains[site]['locationcount'] += 1

        # do the advanced node info stuff
        if self.__isAdvNode__(nodeID,nodeData):
            pass
        print(nodeID)

    def __isAdvNode__(self,nodeID,data):
        try:
            return nodeID in self.advNodeIDs or data['nodeinfo']['advanced-stats']['store-stats']
        except:
            return False

    def __readAdvancedNodesFile__(self,filename):
        advnodes = list()
        if os.path.isfile(filename):
            with open(filename) as f:
                for line in f:
                    advnodes.append(line.split()[0])
        return advnodes

    @staticmethod
    def __domain_dict__():
        return {
            'nodes_count' : 0,
            'nodes_online_count' : 0,
            'locationcount' : 0,
            'firmwarecount' : collections.defaultdict(int),
            'branchcount' : collections.defaultdict(int),
            'autoupdate' : 0,
            'hardwarecount' : collections.defaultdict(int)
        }

    @staticmethod
    def __nested_dict__():
        """Create always nested dict. So we do not have to check whether the parent dict exists."""
        # credits to https://stackoverflow.com/a/36299615
        return collections.defaultdict(DataHandler.__nested_dict__)
