#!/bin/sh
xterm -title "Router 1" -e "python3 protocol.py config.ini" &
xterm -title "Router 2" -e "python3 protocol.py config_2.ini"
