#
# Based on https://tutorialedge.net/python/python-socket-io-tutorial/
#
# Start a webserver that uses websockets PLUS reads from STDIN
#

requires:
  python 3.6
  aiohttp, ...,  pip install aiohttp

Run:
  > ./asyncwebserver/asyncwebserver.py

  App will block in terminal, use CTRL-D to cleanly exit.

Usage:
    * Observe asyncwebserver.log 
    * Open http:/localhost:8080 to view web interface
    * Observe web console for websocker communication
    * Messages from the web interface are send to STDOUT
    * STDIN is monitored and logged to asyncwebserver.log
    * Cleanly shutdown using CTRL-D to STDIN or send a shutdown msg from the web interface
    

