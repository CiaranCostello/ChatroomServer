#!/bin/sh
ip=$(dig +short myip.opendns.com @resolver1.opendns.com)
echo $ip
echo $1
python3 threadedserver.py -p $1 -i $ip