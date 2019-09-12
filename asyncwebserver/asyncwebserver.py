#!/usr/bin/env python3.6
#
# Web server with websockets + does IO via STDIN/STDOUT
#
# Logs to asyncwebserver.log
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
Webserver_loop = None

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
    logging.info("options: {}".format(opts))
    logging.info("args: {}".format(args))

def stdin_reader():
    '''
    Read from STDIN until CTRL-D

    :id int The thread id
    :return None
    '''
    global Verbose

    logging.info("Thread  : stdin_reader is starting")

    for line in sys.stdin:
        logging.info("STDIN   : {}".format(line.rstrip()))

    shutdown_server()

    logging.info("Thread  : stdin_reader is finishing")


def aiohttp_server():
    '''
    Create a web server to send data to STDOUT

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

        response = '{"response":"error", "response-text":"error", "response-code":400}'

        if message.startswith("CMD:"):
            cmd = message[4:]
            if cmd == "SHUTDOWN":
                response = '{"response":"ok", "response-text":"ok", "response-code":200}'
                await sio.emit("message", response)
                print("bye", flush=True) # annouce to server the client is going away
                shutdown_server()
            else:
                pass
        else:
            response = '{"response":"ok", "response-text":"ok", "response-code":200}'
            await sio.emit("message", response)
            print(message, flush=True)

    # We bind our aiohttp endpoint to our app router
    app.router.add_get('/', index_page_handler)

    runner = web.AppRunner(app)
    logging.info("Thread  : aiohttp_server setup exit")
    return runner


def run_server(runner):
    '''
    Start the web server

    :return None
    '''
    global Webserver_loop

    logging.info("Thread  : run_server entry")
    Webserver_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(Webserver_loop)

    # server setup
    Webserver_loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', 8080)
    Webserver_loop.run_until_complete(site.start())
    logging.info("Thread  : run_server start loop")

    # start the server, run until explicitly stopped
    Webserver_loop.run_forever()

    # once stop is called, we run the cleanup task
    Webserver_loop.run_until_complete(runner.cleanup())

    logging.info("Thread  : run_server exit")


def shutdown_server():
    '''
    Stop the web server

    :return None
    '''
    global Webserver_loop

    logging.info("shutdown_server: entry")

    # before stopping the web server, cancel all tasks
    for task in asyncio.Task.all_tasks(Webserver_loop):
        logging.info("shutdown_server: Cancel task")
        Webserver_loop.call_soon_threadsafe(task.cancel)

    # calling Webserver_loop.stop() will not do anything. You must use call_soon_threadsafe()
    Webserver_loop.call_soon_threadsafe(Webserver_loop.stop)


#
# main
#
if __name__ == "__main__":

    # setup logging
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, filename='asyncwebserver.log', filemode='w',  level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Main    : Entry")

    logging.info("Main    : Creating threads ...")

    # start the STDIN reader as a daemon so that it goes away when main exits
    t_stdin_reader = threading.Thread(target=stdin_reader, args=(), daemon=True)

    # the server isn't a daemon because it needs a clean shutdown
    t_webserver = threading.Thread(target=run_server, args=(aiohttp_server(),), daemon=False)

    logging.info("Main    : Creating threads ... done.")

    logging.info("Main    : Starting threads ...")

    t_stdin_reader.start()
    t_webserver.start()

    logging.info("Main    : Starting threads ... done.")

    logging.info("Main    : Waiting for web server thread to finish ...")
    t_webserver.join()
    logging.info("Main    : Waiting for web server thread to finish ... done.")

    logging.info("Main    : Exit")

# end file
