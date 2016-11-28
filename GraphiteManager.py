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

import socket
import time

class GraphiteManager:
    def __init__(self,server,port,domain):
        self.server = server
        self.port = port
        self.domain = domain
        self.message = ""

    def prepareMessage(self, data):
        for i in data['nodes']:
            self.__addHieraDictMessage__(data['nodes'][i], "node.%s" % i)

        self.__addDictMessage__("nodes."+self.domain+".firmware.%s.count",data['firmwarecount'])
        self.__addDictMessage__("nodes."+self.domain+".branch.%s.count", data['branchcount'])
        self.__addDictMessage__("nodes."+self.domain+".hardware.%s.count", data['hardwarecount'])

        self.__addSingleMessage__("nodes."+self.domain+".autoupdate.count",data['autoupdate'])
        self.__addSingleMessage__("nodes."+self.domain+".location.count",data['locationcount'])
        self.__addSingleMessage__("nodes."+self.domain+".total.count",data['nodecount'])
        self.__addSingleMessage__("nodes."+self.domain+".totalclient.count",data['totalclients'])
	self.__addSingleMessage__("nodes."+self.domain+"clients_per_node",data['totalclients']/data['nodecount'])

    def send(self):
        sock = socket.socket()
        sock.connect((self.server, int(self.port)))
        sock.sendall(self.message.encode())
        sock.close()
        pass

    def printout(self):
        print(self.message)

    def __addSingleMessage__(self,key,value):
         self.message += "%s %s %d\n" %(key,value, int(time.time()))

    def __addDictMessage__(self,key,dict):
        for i in dict:
            self.__addSingleMessage__(key % i, dict[i])

    def __addHieraDictMessage__(self,data, path =''):
        for k, v in data.iteritems():
            if isinstance(v, dict):
                self.__addHieraDictMessage__(v, path + '.' + k if len(path) > 0 else k)
            else:
                self.__addSingleMessage__(path + '.' + k, v)

