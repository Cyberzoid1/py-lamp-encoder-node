#!/bin/bash

# get root permission
if [ $EUID != 0 ]; then
    sudo -H "$0" "$@"
    exit $?
fi

# Import .env variables
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ENV_PATH="${DIR}/.env"
if [ -f "${ENV_PATH}" ]; then
  source "${ENV_PATH}"
else
  echo "ERROR: ${ENV_PATH} not found. Copy ${ENV_PATH}-example to ${ENV_PATH}"
  exit
fi

echo "Setup started"

# Setup service user
echo -e "\nUsing ${SERVICE_USER} for service user"
# Create user
sudo useradd --system --shell /sbin/nologin "${SERVICE_USER}"
# pi group reference: https://raspberrypi.stackexchange.com/questions/70214/what-does-each-of-the-default-groups-on-the-raspberry-pi-do
sudo usermod -aG dialout,gpio "${SERVICE_USER}"

# Install Python dependancies
if [[ $* != *-s* ]]; then   # sktp dependancies install when given -s
  echo -e "\nInstalling Python3 and dependancies"
  sudo apt update -q
  sudo apt install -y python3 python3-pip libsystemd-dev wiringpi
  sudo pip3 install -r requirements.txt --upgrade || echo "Pip3 error exiting"; exit
    # Download pygaugette
    if [ -d "py-gaugette" ]; then
      cd py-gaugette
      echo -e "\nPulling latest py-gaugette"
      git pull
      cd ../
    else
      echo -e "\nClonning py-gaugette"
      git clone https://github.com/guyc/py-gaugette.git
      ln -s py-gaugette/gaugette ./gaugette                                 # Use if installing localy
      sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" py-gaugette gaugette  # Remove root as owner
      #./py-gaugette/setup.sh                                               # Installs library system wide
    fi
fi


# Setup systemd unit file
echo -e "\nSetting up system service"
# Note: Imported from .env: SERVICE_NAME, SERVICE_USER, SERVICE_LOG_PATH
# Create a location for logger to write files to
sudo mkdir -p "${SERVICE_LOG_PATH}"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${SERVICE_LOG_PATH}"
sudo chmod -R 774 "${SERVICE_LOG_PATH}"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
# check if a service file already exists and delete if so.
if [ -f "${SERVICE_PATH}" ]; then
  echo -e "\n Removing ${SERVICE_NAME} and replacing with new service"
  sudo rm -v "${SERVICE_PATH}"
fi
sudo cp -v "${SERVICE_NAME}" "${SERVICE_PATH}"       # copy service to systemd directory
sudo chmod 644 "${SERVICE_PATH}"
chmod +x "${SERVICE_PATH}"     # << is this needed?

# Setup systemd unit override file
override="""[Unit]
Description=${SERVICE_DESCRIPTION}
[Service]
User=${SERVICE_USER}
"""
sudo mkdir -p "${SERVICE_PATH}.d"
echo "${override}" > "${SERVICE_PATH}.d/override.conf"

# Load new service file
sudo systemctl daemon-reload
echo -e "\nEnabling and starting service"
sleep 0.2
sudo systemctl enable "${SERVICE_NAME}"
sleep 0.2
sudo systemctl restart "${SERVICE_NAME}"
sleep 0.2
sudo systemctl status "${SERVICE_NAME}"
echo "You can check journalctl output with: 'sudo journalctl -u ${SERVICE_NAME}'"


echo "Setup Complete"
