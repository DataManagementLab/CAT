#!/bin/sh

set -e

# check if python3 is installed
if [[ -z "$(command -v python3)" ]]; then
  printf "Command python3 not found, please install Python >= 3.7.x";
  exit 1;
fi

# check python version
PYV="$(python3 --version | grep -o '[0-9]\.[0-9]\.[0-9]')"
PY_MAJ=${PYV:0:1}
PY_MIN=${PYV:2:1}

if [[ "$PY_MAJ" < 3 ]]; then
  printf "Python version 3 required but found $PYV\n";
  exit 1;
elif [[ "$PY_MIN" < 7 ]]; then
  printf "Python version >= 3.7.x required but found $PYV\n";
  exit 1;
else
  printf "Found compatible Python version $PYV\n";
fi

# check if pip is installed, install otherwise
if [[ -z "$(command -v pip3)" ]]; then
  printf "pip3 not installed, downloading and installing pip\n"
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py;
  python3 get-pip.py;
else
  printf "Found pip3, skipping installation\n"
fi

# install virtualenv
if [[ -z "$(command -v virtualenv)" ]]; then
  pip install virtualenv
else
  printf "Found virtualenv, skipping installation\n";
fi

# setup environment
virtualenv -p python3 .env
source .env/bin/activate
pip install -r requirements.txt

# check node installation
if [[ -z "$(command -v node)" ]]; then
  printf "Could not find a Node.js installation\n";
  exit 1;
else
  printf "Found a Node.js installation\n";
fi

# check npm
if [[ -z "$(command -v npm)" ]]; then
  printf "Could not find a npm installation\n";
  exit 1;
else
  printf "Found a npm installation\n";
fi

# install angular
npm install -g @angular/cli

# install packages into ui folder
npm --prefix ./cat-ui install ./cat-ui