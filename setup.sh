#!/usr/bin/env bash

BASEDIR=$(dirname "$0")
cd $BASEDIR

if [ ! -d venv ]; then
    virtualenv venv
fi

ln -s venv/bin/activate activate
source activate
pip install --upgrade pip
pip install pip-tools
pip-sync
