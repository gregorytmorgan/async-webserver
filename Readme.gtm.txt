#
# Based on https://tutorialedge.net/python/python-socket-io-tutorial/
#
# Start a webserver that uses websockets PLUS reads from STDIN
#

requires:
  python3.6 
  aiohttp,  pip install aiohttp


Start Server:
  > python3.6 asyncwebserver.py

Send message:
     1) open http:/localhost:8080, will block in terminal
     2) Press button
     3) Observer terminal output

