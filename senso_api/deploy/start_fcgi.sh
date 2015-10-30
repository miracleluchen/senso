#!/bin/bash
domain=$1
port=8090
if [ -z $domain ]
then
    echo "domain name is not specified"
    exit 1
fi
ROOT_DIR="/var/www/$domain"

pid=`ps -eo pid,args|grep "python $ROOT_DIR/manage.py runfcgi"|grep -v grep|cut -c1-6|head -1`
if [ -z $pid ]
then
    python $ROOT_DIR/manage.py runfcgi method=prefork host=0.0.0.0 port=$port
    pid=`ps -eo pid,args|grep "python $ROOT_DIR/manage.py runfcgi" |grep -v grep|cut -c1-6|head -1`
    echo "Started,pid=$pid."
else
    echo "FCGI server is already running,pid=$pid."
fi
