#!/bin/bash

# get script's path and cd into that, VM agnostic
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"/.. || exit
echo "current wd: $PWD"


#/home/dev/apps/directions_v2/venv/bin/python -m cronjobs.get_rt_buses_data
/home/ubuntu/apps/directions-service/venv/bin/python -m cronjobs.get_rt_buses_data