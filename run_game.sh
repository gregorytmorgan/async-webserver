#!/bin/sh



if [ -z "$2" ]; then
    TURN_LIMIT=""
else
    TURN_LIMIT="--turn-limit $2"
fi

if [ -z "$1" ]; then
  ./halite --no-timeout $TURN_LIMIT -vvv --width 32 --height 32 "python3 MyDefaultBot.py" "python3 MyDefaultBot.py"
else
  ./halite --no-timeout $TURN_LIMIT -vvv --width 32 --height 32 "python3.6 $1" "python3 MyDefaultBot.py" 
fi

