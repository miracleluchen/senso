#!/bin/bash
set -ef
sh stop_fcgi.sh api.senso.com
sh install_fcgi.sh api.senso.com
sh start_fcgi.sh api.senso.com 
echo "done"
