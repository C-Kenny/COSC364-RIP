#!/bin/sh
xterm -title "Router 1" -e "python3 run.py config_1.ini" &
xterm -title "Router 2" -e "python3 run.py config_2.ini" &
xterm -title "Router 3" -e "python3 run.py config_3.ini" &
xterm -title "Router 4" -e "python3 run.py config_4.ini" &
xterm -title "Router 5" -e "python3 run.py config_5.ini" & 
xterm -title "Router 6" -e "python3 run.py config_6.ini" &
xterm -title "Router 7" -e "python3 run.py config_7.ini"
