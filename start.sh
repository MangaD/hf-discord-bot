#!/bin/bash

source hfbot/bin/activate
python3 -u HFBot.py >> log.txt 2>&1 &
