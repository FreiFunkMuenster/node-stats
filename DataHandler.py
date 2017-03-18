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

import sys, os, collections, json, datetime

class DataHandler(object):
    def __init__(self, jsonData, config):
        self.data = jsonData
        self.config = config
        self._offlineTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=self.config['offline_last_seen_s'])
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
        # print(json.dumps(self.domains, sort_keys=True, indent=4))
        # print(json.dumps(self.nodes, sort_keys=True, indent=4))
        # print(self.gatewayIDs)

    def __operateNode__(self, nodeID, nodeData):

        nodeLastSeen = datetime.datetime.strptime(nodeData['lastseen'], '%Y-%m-%dT%H:%M:%S.%fZ')
        isOnline = nodeLastSeen > self._offlineTime

        nodeInfo = nodeData['nodeinfo']
        nodeStats = nodeData['statistics']
        site = nodeInfo['system']['site_code']
        siteDict = self.domains[site]
        siteDict['nodes_count'] += 1
        nodeGateway = None
        
        # continue if node is online only
        if not isOnline:
            return
        
        siteDict['nodes_online_count'] += 1

        # store all client count type
        if 'clients' in nodeStats:
            for cltype, clcount in nodeStats['clients'].items():
                siteDict['clients_online_count'][cltype] += clcount
            self.nodes[nodeID]['clients_online_count'] = nodeStats['clients']

        if 'gateway' in nodeStats:
            nodeGateway = nodeStats['gateway'].replace(':','')
            if nodeGateway not in self.gatewayIDs:
                self.gatewayIDs.append(nodeGateway)
            siteDict['selected_gateway_count'][nodeGateway] += 1 

        if 'software' in nodeInfo:
            sw = nodeInfo['software']
            # credits to http://stackoverflow.com/a/18578210
            if 'release' in sw.get('firmware', {}):
                siteDict['firmware_count'][sw['firmware']['release']] += 1

            if 'version' in sw.get('batman-adv',{}):
                siteDict['batadv_version_count'][sw['batman-adv']['version']]+= 1

            if 'autoupdater' in sw:
                if 'branch' in sw['autoupdater']:
                    siteDict['branch_count'][sw['autoupdater']['branch']] += 1
                if sw['autoupdater']['enabled']:
                    siteDict['autoupdater_enabled_count'] += 1

        if 'model' in nodeInfo.get('hardware', {}):
            siteDict['hardware_count'][nodeInfo['hardware']['model']] += 1

        if 'location' in nodeInfo:
            siteDict['location_count'] += 1


        # do the advanced node info stuff
        if not self.__isAdvNode__(nodeID,nodeData):
            return

        # statistics
        for key in ('rootfs_usage', 'memory', 'uptime', 'idletime', 'loadavg', 'processes'):
            if key in nodeStats:
                self.nodes[nodeID][key] = nodeStats[key]

        # traffic stats
        if 'traffic' in nodeStats:
            for tkey, tval in nodeStats['traffic'].items():
                stats = {}
                if 'bytes' in tval:
                    stats['if_octets'] = tval['bytes']
                if 'dropped' in tval:
                    stats['if_dropped'] = tval['dropped']
                if 'packets' in tval:
                    stats['if_packets'] = tval['packets']

                if tkey == 'forward':
                    self.nodes[nodeID]['forward'] = stats
                    continue

                if tkey in ('rx', 'tx'):
                    ttype = 'node'
                    tdir = tkey
                elif tkey.startswith('mgmt_'):
                    ttype = 'managed'
                    tdir = tkey.split('_')[1]
                self.nodes[nodeID][ttype][tdir] = stats


        # neighbours
        macTypeMapping = {}
        if 'mesh' in nodeInfo.get('network', {}):
            for batID, batVal in nodeInfo['network']['mesh'].items():
                if 'interfaces' in batVal:
                    for ifType, ifVal in batVal['interfaces'].items():
                        for mac in ifVal:
                            macTypeMapping[mac] = ifType
        for ttype, tvalue in nodeData['neighbours'].items():
            if ttype == 'node_id':
                continue
            for iname, ivalue in tvalue.items():
                if not 'neighbours' in ivalue:
                    continue
                inameid = iname.replace(':', '')
                if iname in macTypeMapping:
                    ifPrefix = macTypeMapping[iname]
                else:
                    ifPrefix = 'unknown'
                for nname, nvalue in ivalue['neighbours'].items():
                    nnameid = nname.replace(':', '')
                    self.nodes[nodeID][ttype][''.join((ifPrefix, '_', inameid))][nnameid] = nvalue


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
            'clients_online_count' : collections.defaultdict(int),
            'location_count' : 0,
            'firmware_count' : collections.defaultdict(int),
            'branch_count' : collections.defaultdict(int),
            'autoupdater_enabled_count' : 0,
            'hardware_count' : collections.defaultdict(int),
            'selected_gateway_count' : collections.defaultdict(int),
            'batadv_version_count' : collections.defaultdict(int)
        }

    @staticmethod
    def __nested_dict__():
        """Create always nested dict. So we do not have to check whether the parent dict exists."""
        # credits to https://stackoverflow.com/a/36299615
        return collections.defaultdict(DataHandler.__nested_dict__)
