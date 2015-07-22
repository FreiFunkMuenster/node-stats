#!/bin/bash

for i in `seq 1 6`;
do
  python /var/node-stats/main.py -server 10.43.0.12 -port 2003
  sleep 10
done


