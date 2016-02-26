#
# (c) 2015 dray <dresen@itsecteam.ms>
#
# This script is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License or any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
#

from subprocess import check_output
import json
import sys

class JsonManager:
    def __init__(self):
        self.advStats = {}
        self.json158 = []
        self.json159 = []
        self.json159 = []
        self.result = {}
        pass


    def loadJson(self):
        data=""
        for l in open("alfred_158.json"):
            data += l
        self.json158 = json.loads(data)
        data=""
        for l in open("alfred_159.json"):
            data += l
        self.json159 =json.loads(data)
        data=""
        for l in open("alfred_160.json"):
            data += l
        self.json160 =json.loads(data)


    def loadJsonFromAlfred(self, socket):
        self.json158 = json.loads(check_output(["alfred-json", "-z","-r","158","-s",socket]).decode("utf-8"))
        self.json159 = json.loads(check_output(["alfred-json", "-z","-r","159","-s",socket]).decode("utf-8"))
        self.json160 = json.loads(check_output(["alfred-json", "-z","-r","160","-s",socket]).decode("utf-8"))


    def processJson158(self):
        self.result["autoupdate"] = 0
        for id in self.json158:
            node = self.json158[id]

    # Nodes/Firmware
            if 'software' in node:
                firmware = node['software']['firmware']['release']
                self.__incCounter__('firmwarecount',firmware)
                if 'autoupdater' in node['software']:
                    branch = node['software']['autoupdater']['branch']
                    self.__incCounter__('branchcount',branch)

                    if node['software']['autoupdater']['enabled']:
                        self.__incCounter__('autoupdate')

            if 'hardware' in node:
                hardware = node['hardware']['model']
                self.__incCounter__('hardwarecount',hardware)

            if 'location' in node:
                self.__incCounter__('locationcount')
            try:
                if node['advanced-stats']['store-stats'] == True:
                    self.advStats[id] = True
            except:
                self.advStats[id] = False



        self.result['nodecount'] = len(self.json158)


    def processJson159(self):
        self.result['nodes'] = {}
        self.result['totalclients']=0
        for id in self.json159:

            node = self.json159[id]
            nodeID = node['node_id']

    # Nodes/Gateway
            try:
                if 'mesh_vpn' in node and 'domaene_01' in node['mesh_vpn']['groups']:
                    peers = node['mesh_vpn']['groups']['domaene_01']['peers']
                    for x in peers:
                        if peers[x]:
                            self.__incCounter__('gateway',x)
            except:
                pass
                sys.stderr.write("Error %s" % sys.exc_info()[0])

    # Client/Node
            
            self.result['nodes'][nodeID] = {}
            try:
                if 'clients' in node:
                    self.result['nodes'][nodeID]["count"] = node['clients']['total']
                    self.result['totalclients'] += node['clients']['total']
            except:
                sys.stderr.write("Error %s" % sys.exc_info()[0])

            try:
                if id in self.advStats and self.advStats[id] == True:
                    self.result['nodes'][nodeID].update(self.processAdvancedStats159(node))
            except:
                sys.stderr.write("Error %s" % sys.exc_info()[0])


    def processJson160(self):
        for id, node in self.json160.iteritems():
            if id in self.advStats and self.advStats[id] == True:
                node_id = node['node_id']
                try:
                    if 'wifi' in node:
                        self.result['nodes'][node_id]['wifi'] = self.__wifiBatStats__(node['wifi'], ['noise', 'inactive', 'signal'])
                    if 'batadv' in node:
                        self.result['nodes'][node_id]['batadv'] = self.__wifiBatStats__(node['batadv'], ['tq', 'lastseen'])
                except:
                    sys.stderr.write("Error %s" % sys.exc_info()[0])


    def __wifiBatStats__(self, data, keys):
        dataStats = {
            'count' : 0
        }
        for if_id, if_val in data.iteritems():
            if_id_print = if_id.replace(':', '_')
            dataStats[if_id_print] = {
                'count' : 0
            }
            if if_val and 'neighbours' in if_val:
                for neigh_id, neigh_val in data[if_id]['neighbours'].iteritems():
                    dataStats['count'] += 1
                    dataStats[if_id_print]['count'] += 1
                    dataStats[if_id_print][neigh_id.replace(':','_')] = self.__cherryPickEntries__(neigh_val, keys)
        return dataStats


    def processAdvancedStats159(self, node):
        advancedStats = {}

        #add data, where no procession or conversion is needed
        entries = [
            'uptime',
            'idletime', 
            'loadavg', 
            [ 'memory',
                [
                    'cached',
                    'buffers',
                    'total',
                    'free'
                ]
            ],
            [ 'clients',
                [
                    'total',
                    'wifi'
                ]
            ],
            [ 'processes',
                [
                    'running',
                    'total'
                ]
            ]
        ]

        advancedStats.update(self.__cherryPickEntries__(node,entries))

        # add traffic stats
        if 'traffic' in node:
            advancedStats['traffic'] = {}
            if 'rx' in node['traffic'] and 'tx' in node['traffic']:
                advancedStats['traffic']['all'] = self.__ifStats__(node['traffic']['rx'], node['traffic']['tx'])
            if 'mgmt_rx' in node['traffic'] and 'mgmt_tx' in node['traffic']:
                advancedStats['traffic']['managed'] = self.__ifStats__(node['traffic']['mgmt_rx'], node['traffic']['mgmt_tx'])
            if 'forward' in node['traffic']:
                advancedStats['traffic']['forward'] = self.__ifStats__(node['traffic']['forward'])
        # add vpn stats
        if 'mesh_vpn' in node:
                advancedStats.update(self.__vpnStats__(node['mesh_vpn']))
        if 'gateway' in node:
            advancedStats['bat_gw_id'] = node['gateway'].split(':')[-1]
        return advancedStats


    def __vpnStats__(self,data):
        dataStats = {}
        if 'groups' in data:
            for gname, group in data['groups'].iteritems():
                dataStats[gname] = {}
                if 'peers' in group:
                    for pname, peer in group['peers'].iteritems():
                        if peer and 'established' in peer:
                            dataStats[gname][pname] = peer['established']
                        else:
                            dataStats[gname][pname] = 0
        return dataStats


    def __ifStats__(self,rx,tx = None):
        mapping = {
            'bytes' : 'if_octets',
            'dropped' : 'if_dropped',
            'packets' : 'if_packets'
        }
        ifaceStats = {}
        for k, v in mapping.iteritems():
            if rx and k in rx or tx and k in tx:
                ifaceStats[v] = {}
                if rx and tx:
                    if k in rx:
                        ifaceStats[v]['rx'] = rx[k]
                    if k in tx:
                        ifaceStats[v]['tx'] = tx[k]
                elif k in rx:
                    ifaceStats[v] = rx[k]
        return ifaceStats


    def __cherryPickEntries__(self, data, entries):
        dataStats = {}
        for entry in entries:
            if isinstance(entry, list):
                if entry[0] in data:
                    dataStats[entry[0]] = (self.__cherryPickEntries__(data[entry[0]], entry[1]))
            else:
                if entry in data:
                    dataStats[entry] = data[entry]
        return dataStats


    def __incCounter__(self, key, value=None):

        if value is None:
            if key not in self.result:
                self.result[key] = 0
            self.result[key]+=1
        else:
            value = self.___cleanstr___(value)
            if key not in self.result:
                self.result[key] = {}
            if value in self.result[key]:
                self.result[key][value]+=1
            else:
                self.result[key][value]=1


    def ___cleanstr___(self, cleanstr):
        specialChars = [" ","+",".","\\","/","-"]
        for char in specialChars:
            cleanstr = cleanstr.replace(char,"_")
        cleanstr = cleanstr.replace(":","")
        return cleanstr

