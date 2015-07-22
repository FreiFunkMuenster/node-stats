#!/usr/bin/env python
#
# (c) 2015 dray <dresen@itsecteam.ms>
#
# This script is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
#
#

import json
import socket
import time
from subprocess import check_output
import argparse

parser = argparse.ArgumentParser(description='This Script gets information about Freifunk Muenster')
parser.add_argument('-server', required=True, help='Server')
parser.add_argument('-port', required=True, help='Port')
args = parser.parse_args()

gatewaycount = {}
firmwarecount = {}
branchcount = {}
hardwarecount = {}
nodecount=0
autoupdatecount=0
nodes ={}
locationcount=0


dataJson = check_output(["alfred-json", "-z","-r","159"])
for l in open("slfred_159.json"):
    dataJson += l

data = json.loads(dataJson)

for id in data:
    node = data[id]

    # Nodes/Gateway

    if 'mesh_vpn' in node:
        tmp = node['mesh_vpn']['groups']['backbone']['peers']
        for x in tmp:
            if tmp[x]:
                if x in gatewaycount:
                    gatewaycount[x]+=1
                else:
                    gatewaycount[x]=1
#    if 'gateway' in node:
#        if node['gateway'] in gatewaycount:
#            gatewaycount[node['gateway']]+=1
#        else:
#            gatewaycount[node['gateway']] = 1

    # Client/Node
    id = node['node_id']
    nodes[id] = {}
    if 'clients' in node:
        nodes[id]["clientcount"] = node['clients']['wifi']


"""
dataJson=""
for l in open("slfred_158.json"):
    dataJson += l
"""
dataJson = check_output(["alfred-json", "-z","-r","158"])
data = json.loads(dataJson)

for id in data:
    node = data[id]

    # Nodes/Firmware
    if 'software' in node:
        firmware = node['software']['firmware']['release']
        if firmware in firmwarecount:
            firmwarecount[firmware] += 1
        else:
            firmwarecount[firmware] = 1

        branch = node['software']['autoupdater']['branch']
        if branch in branchcount:
            branchcount[branch] += 1
        else:
            branchcount[branch] = 1
        if node['software']['autoupdater']['enabled']:
            autoupdatecount+=1

    if 'hardware' in node:
        hardware = node['hardware']['model']
        if hardware in hardwarecount:
            hardwarecount[hardware] += 1
        else:
            hardwarecount[hardware] = 1

    if 'location' in node:
        locationcount+=1

nodecount = len(data)


"""
print(nodes)
print(gatewaycount)
print(firmwarecount)
print(nodecount)
print(branchcount)
print("Nodes/Branch %s" % str(branchcount))
print("Nodes with Autoupdate %d" % autoupdatecount)
print("Nodes/Hardware: %s" % str(hardwarecount))
print("Node with Location: %s" % (str(locationcount)))
"""

def clean(cleanstr):
    b = [" ","+",".","\\","/","-"]
    for a in b:
        cleanstr = cleanstr.replace(a,"_")
    cleanstr = cleanstr.replace(":","")
    return cleanstr

sock = socket.socket()
sock.connect((args.server, args.port))
for i in nodes:
    if 'clientcount' in nodes[i]:
        message = "node.%s.count %s %d\n" %(i,nodes[i]['clientcount'], int(time.time()))
        sock.sendall(message.encode())

for i in firmwarecount:
    message = "nodes.firmware.%s.count %s %d\n" %(clean(i).replace(".","_").replace("+","_"), firmwarecount[i], int(time.time()))
    sock.sendall(message.encode())

"""
for i in gatewaycount:
    message = "nodes.gateway.%s.count %s %d\n" %(clean(i),gatewaycount[i], int(time.time()))
    sock.sendall(message.encode())
"""
for i in branchcount:
    message = "nodes.branch.%s.count %s %d\n" %(clean(i),branchcount[i], int(time.time()))
    sock.sendall(message.encode())

for i in hardwarecount:
    message = "nodes.hardware.%s.count %s %d\n" %(clean(i), hardwarecount[i], int(time.time()))
    sock.sendall(message.encode())

message = "nodes.autoupdate.count %s %d\n" %(autoupdatecount, int(time.time()))
sock.sendall(message.encode())

message = "nodes.location.count %s %d\n" %(locationcount, int(time.time()))
sock.sendall(message.encode())

message = "nodes.total.count %s %d\n" %(nodecount, int(time.time()))
sock.sendall(message.encode())

sock.close()
