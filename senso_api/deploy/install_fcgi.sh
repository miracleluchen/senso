#!/bin/bash
set -ef

domain=$1
if [ -z $domain ]
then
    echo "domain name is not specified"
    exit 1
fi
ROOT_DIR="/var/www/$domain"


if [ -d $ROOT_DIR ]
then
    echo "back up "$domain" ..."
    mv $ROOT_DIR $ROOT_DIR-`date +%Y_%m_%d_%H_%M_%S`
fi

mkdir $ROOT_DIR
cp -r ../ $ROOT_DIR/


