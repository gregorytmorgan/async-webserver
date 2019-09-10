#
# Based on https://tutorialedge.net/python/python-socket-io-tutorial/
#
# Start a webserver that uses websockets PLUS reads from STDIN
#

requires:
  python 3.6
  aiohttp, ...,  pip install aiohttp


Start Server:
  > python3.6 asyncwebserver.py

Send message:
     1) open http:/localhost:8080, will block in terminal, use CTRL-D to cleanly exit.
     2) Send a message via HTML input
     3) Observer terminal output and console logs

