#!/usr/bin/env python3
# -*- coding: utf8 -*-
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
#

import argparse, os
from JsonManager import JsonManager
from GraphiteManager import GraphiteManager

parser = argparse.ArgumentParser(description='This Script gets information about Freifunk Muenster')
parser.add_argument('--server', required=True, help='Server')
parser.add_argument('--port', required=True, help='Port', default=2003)
parser.add_argument('--batif', required=True, help='Batman interface', default='bat0')
parser.add_argument('--domain', help='Freifunk Domäne', default='legacy')
parser.add_argument('--local', help='Load local json files (alfred_158.json,alfred_159.json)', action='store_true')
parser.add_argument('--print-only', help='Print only', action='store_true')
args = parser.parse_args()

jsonManager = JsonManager()
if args.local:
    jsonManager.loadJson()
else:
    jsonManager.loadJsonFromRespondd(args.batif)
jsonManager.processJson158()
jsonManager.processJson159()
jsonManager.processJson160()

graphiteManager = GraphiteManager(args.server, args.port, args.domain)
graphiteManager.prepareMessage(jsonManager.result)

if args.print_only:
    graphiteManager.printout()
else:
    graphiteManager.send()
