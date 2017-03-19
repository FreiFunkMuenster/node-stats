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
        self.advNodeIDs =  self.config['adv_node_stats']
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
        print(json.dumps(self.domains, sort_keys=True, indent=4, default=AvgEntry.cdefault))
        # print(json.dumps(self.nodes, sort_keys=True, indent=4))
        # print(self.gatewayIDs)

    def __operateNode__(self, nodeID, nodeData):

        nodeLastSeen = datetime.datetime.strptime(nodeData['lastseen'], '%Y-%m-%dT%H:%M:%S.%fZ')
        isOnline = nodeLastSeen > self._offlineTime

        nodeInfo = nodeData['nodeinfo']
        nodeStats = nodeData['statistics']
        site = nodeInfo['system']['site_code']

        # avoid dots
        siteDict = self.domains[site]
        nodeDict = self.nodes[nodeID]

        nodeGateway = None
        nodeGatewayNexthop = None

        siteDict['nodes_count']['nodes_all'] += 1
        
        # continue if node is online only
        if not isOnline:
            return
        
        siteDict['nodes_count']['nodes_online'] += 1


        if 'model' in nodeInfo.get('hardware', {}):
            siteDict['hardware'][nodeInfo['hardware']['model']] += 1

        if 'location' in nodeInfo:
            siteDict['nodes_count']['has_location'] += 1

        if 'contact' in nodeInfo.get('owner', {}):
            siteDict['nodes_count']['has_contact'] += 1

        # store all client count type
        if 'clients' in nodeStats:
            for cltype, clcount in nodeStats['clients'].items():
                siteDict['clients_online'][cltype] += clcount
            nodeDict['clients_online'] = nodeStats['clients']

        # infos about gateway and next hop
        if 'gateway' in nodeStats:
            nodeGateway = nodeStats['gateway'].replace(':','')
            if 'gateway_nexthop' in nodeStats:
                nodeGatewayNexthop = nodeStats['gateway_nexthop'].replace(':','')
                if nodeStats['gateway'] == nodeStats['gateway_nexthop']:
                    siteDict['nodes_count']['nodes_with_uplink'] += 1
                else:
                    siteDict['nodes_count']['nodes_mesh_only'] += 1
            if nodeGateway not in self.gatewayIDs:
                self.gatewayIDs.append(nodeGateway)
            siteDict['selected_gateway'][nodeGateway] += 1 

        # infos about firmware and autoupdater
        if 'software' in nodeInfo:
            sw = nodeInfo['software']
            # credits to http://stackoverflow.com/a/18578210
            if 'release' in sw.get('firmware', {}):
                siteDict['firmware']['release'][sw['firmware']['release']] += 1

            if 'base' in sw.get('firmware', {}):
                siteDict['firmware']['base'][sw['firmware']['base']] += 1

            if 'version' in sw.get('batman-adv',{}):
                siteDict['batadv_version'][sw['batman-adv']['version']]+= 1

            if 'autoupdater' in sw:
                if 'branch' in sw['autoupdater']:
                    siteDict['branch'][sw['autoupdater']['branch']] += 1
                if sw['autoupdater']['enabled']:
                    siteDict['autoupdater_enabled'] += 1


        # avg stats
        for key in ('uptime', 'idletime', 'loadavg'):
            if key in nodeStats:
                siteDict['averages'][key].append(nodeStats[key])

        # avg gateway and gateway_nexthop tq
        if 'batadv' in nodeData['neighbours']:
            for iname, ivalue in nodeData['neighbours']['batadv'].items():
                if not 'neighbours' in ivalue:
                    continue
                for nname, nvalue in ivalue['neighbours'].items():
                    nnameid = nname.replace(':', '')
                    if nnameid == nodeGateway:
                        if 'tq' in nvalue:
                            siteDict['averages']['gateway_uplink_tq'].append(nvalue['tq'])
                    elif nnameid == nodeGatewayNexthop:
                        if 'tq' in nvalue:
                            siteDict['averages']['gateway_nexthop_tq'].append(nvalue['tq'])

        # do the advanced node info stuff
        if not self.__isAdvNode__(nodeID,nodeData):
            return

        # statistics
        for key in ('rootfs_usage', 'memory', 'uptime', 'idletime', 'loadavg', 'processes'):
            if key in nodeStats:
                nodeDict[key] = nodeStats[key]

        # traffic stats
        if 'traffic' in nodeStats:
            for tkey, tval in nodeStats['traffic'].items():
                stats = {}

                # map traffic stats to graphite format
                if 'bytes' in tval:
                    stats['if_octets'] = tval['bytes']
                if 'dropped' in tval:
                    stats['if_dropped'] = tval['dropped']
                if 'packets' in tval:
                    stats['if_packets'] = tval['packets']

                # forward traffic has no direction
                if tkey == 'forward':
                    nodeDict['traffic']['forward'] = stats
                    continue

                # handle node and managed traffic for both rx and tx
                if tkey in ('rx', 'tx'):
                    ttype = 'node'
                    tdir = tkey
                elif tkey.startswith('mgmt_'):
                    ttype = 'managed'
                    tdir = tkey.split('_')[1]
                nodeDict['traffic'][ttype][tdir] = stats


        # neighbours

        # generate type mapping for interface
        macTypeMapping = {}
        if 'mesh' in nodeInfo.get('network', {}):
            for batID, batVal in nodeInfo['network']['mesh'].items():
                if 'interfaces' in batVal:
                    for ifType, ifVal in batVal['interfaces'].items():
                        for mac in ifVal:
                            macTypeMapping[mac] = ifType
        # print(macTypeMapping)

        # get informations about interfaces and neighbours for both batadv and wifi
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
                ifDict = nodeDict[ttype]['interfaces'][''.join((ifPrefix, '_', inameid))]
                for nname, nvalue in ivalue['neighbours'].items():
                    nnameid = nname.replace(':', '')
                    if nnameid == nodeGateway:
                        nodeDict[ttype]['gateway'][nnameid] = nvalue
                    elif nnameid == nodeGatewayNexthop:
                        nodeDict[ttype]['gateway_nexthop'][nnameid] = nvalue
                    ifDict['links'][nnameid] = nvalue
                ifDict['count'] = len(ifDict['links'])
            ifDict = nodeDict[ttype]['count'] = len(nodeDict[ttype]['interfaces'])


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
            'nodes_count' : collections.defaultdict(int),
            'averages' : collections.defaultdict(AvgEntry),
            'clients_online' : collections.defaultdict(int),
            'firmware' : {
                'release' : collections.defaultdict(int),
                'base' : collections.defaultdict(int)
            },
            'branch' : collections.defaultdict(int),
            'autoupdater_enabled' : 0,
            'hardware' : collections.defaultdict(int),
            'selected_gateway' : collections.defaultdict(int),
            'batadv_version' : collections.defaultdict(int)
        }

    @staticmethod
    def __nested_dict__():
        """Create always nested dict. So we do not have to check whether the parent dict exists."""
        # credits to https://stackoverflow.com/a/36299615
        return collections.defaultdict(DataHandler.__nested_dict__)

class AvgEntry(object):
    def __init__(self):
        self._dataset = []

    def append(self, val):
        self._dataset.append(val)

    def avg(self):
        if not self._dataset:
            return 0
        return sum(self._dataset)/float(len(self._dataset))

    # overloading str() operator so no changes to DataHandler are required
    def __str__(self):
        return '{0}'.format(self.avg())

    @staticmethod
    def cdefault(o):
        if isinstance(o, AvgEntry):
            return str(o)
        return o.__dict__