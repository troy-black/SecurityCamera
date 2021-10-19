#!/bin/bash

# Default variables
APP="SecurityCamera"

# System variables
OS="unknown"
VERSION="unknown"
PYTHON="python3"
VENV_ACTIVATION="source venv/bin/activate"

updateVenv() {
  if [ "${PWD##*/}" == "${APP}" ] && [ -d "venv" ]; then
    ${VENV_ACTIVATION}

    # update pip
    python -m pip install --upgrade pip

    # install python libs
    pip install -r requirements.txt

    # link Gstreamer Python from /usr/lib/
    ln -s /usr/lib/python3/dist-packages/gi venv/lib/python*/site-packages
  fi
}

createVenv() {
  if [[ "${PWD##*/}" == "${APP}" ]]; then
    if [[ -d "venv" ]]; then
      rm -rf venv
    fi
    "${PYTHON}" -m venv venv
    updateVenv
  fi
}

getOs() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
  else
    OS=$(uname -s)
    # VERSION=$(uname -r)
    case "${OS}" in
    CYGWIN* | MINGW*)
      OS="Windows"
      PYTHON="python"
      VENV_ACTIVATION="source venv/Scripts/activate"
      ;;
    esac
  fi
}

updateOs() {
  sudo apt -y update
  sudo apt -y upgrade
}

help() {
  echo "
        usage:
        -----
        setup.sh [ n ] [ s ] [ v ] [ h ]
        description:
        ----------
        Setup bash script for ${APP}
        ---------------
        n | nano            Install Jestson Nano requirements with ArduCAM IMX477 cams.
        s | service         Create systemd service to run at startup.
        v | venv            Create new python virtual environment.
        h | help            This helpful bit of info.
        "
}

newVenv() {
  # enable verbose and exit on error
  set -x
  getOs
  createVenv
}

installGstreamer() {
  sudo add-apt-repository universe -y
  sudo add-apt-repository multiverse -y
  sudo apt-get update -y
  sudo apt-get install -y gstreamer1.0-tools gstreamer1.0-alsa gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
  sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev libgstreamer-plugins-bad1.0-dev
}

installGstreamerPython() {
  #  https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Python_Sample_Apps.html
  sudo apt-get install -y python-gi-dev
  export GST_LIBS="-lgstreamer-1.0 -lgobject-2.0 -lglib-2.0"
  export GST_CFLAGS="-pthread -I/usr/include/gstreamer-1.0 -I/usr/include/glib-2.0 -I/usr/lib/x86_64-linux-gnu/glib-2.0/include"
  git clone https://github.com/GStreamer/gst-python.git
  cd gst-python
  git checkout 1a8f48a
  ./autogen.sh PYTHON=python3
  ./configure PYTHON=python3
  make
  sudo make install
  cd ../
}

installArduCamImx477Driver() {
  # ArduCAM IMX477 Driver
  wget https://github.com/ArduCAM/MIPI_Camera/releases/download/v0.0.3/install_full.sh
  chmod +x install_full.sh
  # Install and reboot
  yes | ./install_full.sh -m imx477
}

setTerminalStartup() {
  sudo systemctl set-default multi-user.target
}

setupAppService() {
  sudo cp securitycamera.service /etc/systemd/system/securitycamera.service
  systemctl enable securitycamera.service
}

setupNano() {
  getOs

  if [[ "${OS}" == "Ubuntu" ]] && [[ "${VERSION}" == "18.04" ]]; then
    updateOs

    installGstreamer
    installGstreamerPython

    setTerminalStartup

    # This will cause reboot
    installArduCamImx477Driver
  fi
}

case "$1" in
u | nano)
  setupNano
  ;;
s | service)
  setupAppService
  ;;
v | venv)
  newVenv
  ;;
h | help | *)
  help
  ;;
esac

set +ex
