#!/bin/bash
# This script is for convienence

# get root permission
if [ $EUID != 0 ]; then
    sudo -H "$0" "$@"
    exit $?
fi

case $1 in
start)
  sudo systemctl start lamp.service
  sudo systemctl status lamp.service
  ;;
stop)
  sudo systemctl stop lamp.service
  ;;
restart)
  sudo systemctl restart lamp.service
  ;;
status)
  sudo systemctl status lamp.service
  ;;
recent)
  sudo journalctl -u lamp.service --since "5 minutes ago" -n 70
  ;;
log)
  sudo journalctl -u lamp.service -n 70
  ;;
*)
  echo "Arguments start|stop|restart|status|recent|log"
esac
