#!/usr/bin/env python3.6
#
# Web server using websockets + does IO via STDIN/STDOUT
#
# Ref:
#   Python Socket.io Tutorial: https://tutorialedge.net/python/python-socket-io-tutorial/
#

import sys
import getopt
import socketio
import asyncio
import logging
import threading

from aiohttp import web

Verbose = False
Loop = None

def usage():
    program_name = sys.argv[0]
    print("Usage: {} [options]".format(program_name))
    print("  -h\tHelp.")
    print("  -v\tVerbose.")

try:
   opts, args = getopt.getopt(sys.argv[1:] , "hv", ["help", "verbose"])
except getopt.GetoptError:
   usage()
   sys.exit(2)

if len(args) > 0:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-v":
        Verbose = True
    elif o in ("-h", "--help"):
        usage()
        sys.exit(0)
    else:
        assert False, "unhandled option"

if Verbose:
    print("options: {}".format(opts))
    print("args: {}".format(args))

def reverse_string(id):
    '''
    Take a string in from STDIN, reverse it and output to STDOUT

    :id int The thread id
    :return None
    '''
    global Verbose

    logging.info("Thread  : Reverser %d is starting", id)

    for line in sys.stdin:
        print("{}".format(line.rstrip()[::-1]))

    logging.info("Thread  : Reverser %d is finishing", id)


def aiohttp_server():
    '''
    :return None

    '''
    logging.info("Thread  : aiohttp_server setup entry")

    # creates a new Async Socket IO Server
    sio = socketio.AsyncServer()

    # Creates a new Aiohttp Web Application
    app = web.Application()

    # Binds our Socket.IO server to our Web App instance
    sio.attach(app)

    # we can define aiohttp endpoints just as we normally would with no change
    async def index_page_handler(request):
        with open('index.html') as f:
            return web.Response(text=f.read(), content_type='text/html')

    # If we wanted to create a new websocket endpoint, use this decorator,
    # passing in the name of the event we wish to listen out for
    @sio.on('message')
    async def print_message(sid, message):
        # When we receive a new event of type 'message' through a socket.io connection
        # we print the socket ID and the message
        logging.info("Socket ID: %s", sid)
        logging.info("Message: %s", message)
        await sio.emit('message', message[::-1])

    # We bind our aiohttp endpoint to our app router
    app.router.add_get('/', index_page_handler)

    runner = web.AppRunner(app)
    logging.info("Thread  : aiohttp_server setup exit")
    return runner

def run_server(runner):
    '''
    Start a web server using 'runner'

    :return None
    '''
    global Loop

    logging.info("Thread  : run_server entry")
    Loop = asyncio.new_event_loop()
    asyncio.set_event_loop(Loop)
    Loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', 8080)
    Loop.run_until_complete(site.start())
    logging.info("Thread  : run_server start loop")

    # start the server, run until stopped
    Loop.run_forever()

    # once stop is called, we run the cleanup task
    Loop.run_until_complete(runner.cleanup())

    logging.info("Thread  : run_server exit")

#
# main
#
if __name__ == "__main__":

    # setup logging
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Main    : Entry")

    logging.info("Main    : Before creating threads")
    t_reverse = threading.Thread(target=reverse_string, args=(1,))
    t_webserver = threading.Thread(target=run_server, args=(aiohttp_server(),)) # , daemon=True

    logging.info("Main    : Before starting threads.")
    t_reverse.start()
    t_webserver.start()

    logging.info("Main    : Threads started. Waiting for the threads to finish.")

    logging.info("Main    : Before reverser join().")
    t_reverse.join()

    #
    # Reverse (stdin/stdout IO) will block until ctrl-D. Once ctrl-D is recv, reverse will
    # exit/join.
    #

    logging.info("Main    : After reverser join().")

    #
    # Once reverser exits, we stop the web server

    if not Loop is None:
        # before stopping the web server, cancel all tasks
        for task in asyncio.Task.all_tasks(Loop):
            logging.info("Main    : Cancel task")
            task.cancel()

        # calling Loop.stop() will not do anything. You must use call_soon_threadsafe()
        Loop.call_soon_threadsafe(Loop.stop)

        logging.info("Main    : Before web server join().")

        t_webserver.join() # necessary?

        Loop.close() # necessary?

        logging.info("Main    : After web server join().")
    else:
        logging.info("Main    : No loop exists")

    logging.info("Main    : Exit")


# end file
