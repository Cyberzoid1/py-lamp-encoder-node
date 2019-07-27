#!/bin/bash

# get root permission
if [ $EUID != 0 ]; then
    sudo -H "$0" "$@"
    exit $?
fi

# Import .env variables
ENV_PATH=".env"
if [ -f "${ENV_PATH}" ]; then
  source "${ENV_PATH}"
else
  echo "ERROR: ${ENV_PATH} not found. Copy ${ENV_PATH}-example to ${ENV_PATH}"
  exit
fi

echo "Setup started"


# Install Python dependancies
sudo apt update -q
sudo apt install python3 python3-pip
sudo pip3 install -r requirements.txt

  # Download pygaugette
  git clone https://github.com/guyc/py-gaugette.git
  ln -s py-gaugette/gaugette ./gaugette       # Use if installing localy
  #./py-gaugette/setup.sh                        # Installs library system wide


# Setup systemd unit file
echo -e "\nSetting up system service"
# Note: Imported from .env: SERVICE_NAME, SERVICE_USER, SERVICE_LOG_PATH
# Create a location for logger to write files to
sudo mkdir -p "${SERVICE_LOG_PATH}"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${SERVICE_LOG_PATH}"
SERVICE_PATH="/lib/systemd/system/$SERVICE_NAME"
# check if a service file already exists and delete if so.
if [ -f "${SERVICE_PATH}" ]; then
  echo -e "\n Removing ${SERVICE_NAME} and replacing with new service"
  sudo rm -v "${SERVICE_PATH}"
fi
sudo cp -v "${SERVICE_NAME}" "${SERVICE_PATH}"       # copy service to systemd directory
sudo chmod 644 "${SERVICE_PATH}"
chmod +x "${SERVICE_PATH}"     # << is this needed?

# Load new service file
sudo systemctl daemon-reload
echo "Enabling and starting service"
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"
echo "You can check journalctl output with: 'sudo journalctl -u ${SERVICE_NAME}'"


echo "Setup Complete"