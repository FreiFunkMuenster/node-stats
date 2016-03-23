#!/bin/bash
for i in /proc/sys/net/ipv4/conf/bat*; do
    num=${i#*bat}
    python /usr/src/node-stats/main.py --server=localhost --port=2003 --domain=domaene-${num} --socket=/run/alfred.${num}.sock
done
