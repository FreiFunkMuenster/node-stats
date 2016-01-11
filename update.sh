#!/bin/bash
for i in /proc/sys/net/ipv4/conf/bat*; do
    num=${i#*bat}
    python /usr/src/node-stats/main.py --server=192.168.43.1 --port=2003 --domain=domaene-$(printf %02d ${num}) --socket=/run/alfred.$(printf %02d ${num}).sock
done
