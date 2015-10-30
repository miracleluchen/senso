#!/bin/bash

domain=$1
if [ -z $domain ]
then
    echo "domain name is not specified"
    exit 1
fi
ROOT_DIR="/var/www/$domain"

pids=0
pids=`ps aux | grep "python $ROOT_DIR/manage.py runfcgi" | grep -v grep | awk '{print $2}'`

if [ "$pids" = ""  ]
then
    echo "FCGI server is not running, do nothing."
else
    echo `date` ": FCGI server is running now, pids=" $pids
    echo -n `date` ": Killing them now..."

    for pid in $pids
    do
        echo -n " "$pid
        kill -9 $pid
    done
    echo
    echo `date` ": Stopped."
fi
