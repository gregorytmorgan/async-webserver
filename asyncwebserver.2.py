#!/usr/bin/env python3.6
#
# Web server with websocket/socket.io exploration
#

import sys
import logging
import threading
import aiohttp_cors
import time
import json

# https://python-socketio.readthedocs.io/en/latest/index.html
import socketio

# https://docs.python.org/3.6/library/asyncio.html
# used to manage the aiohttp server tasks, get the async event loop
import asyncio

# Used to asynchronously spawn a web server response thread
from concurrent.futures import ThreadPoolExecutor

# https://docs.aiohttp.org/en/stable/index.html
# used for base web server
from aiohttp import web

# creates a new Async Socket.IO Server (note: socket.io is not strictly a websocket server)
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*') # , async_handlers=True will prevent queueing of messages from a single client

#
# globals
#
app =  None

logfile = 'asyncwebserver.2.log'

server_address = "localhost"
server_port = "8080"

Webserver_loop = None

# delay/block in the long_request hander for n seconds
long_request_delay = 4

tp_executor = ThreadPoolExecutor(max_workers = 2)

logging.basicConfig(
    format="%(asctime)s: %(message)s",
    filename=logfile,
    filemode='w',
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

#
# helper methods
#

def shutdown_server():
    '''
    Stop the web server

    Cancels all the asyncio tasks. Once the web server exits, the main process
    will exit as well.

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


def block_for(secs):
    '''
    Block / return after secs seconds have passed.

    :secs integer Delay in seconds.
    :return string
    '''
    logging.info("block_for - entry({})".format(secs))

    time.sleep(secs)

    logging.info("block_for - exit")

    return "block_for done"


def aiohttp_init():
    '''
    Create a web server

    :return web.AppRunner
    '''
    global sio
    global app

    logging.info("aiohttp_init - entry")

    # Creates a new Aiohttp Web Application
    app = web.Application()

    app['connections'] = {}

    # register state change handlers
    app.on_startup.append(startup)
    app.on_shutdown.append(cleanup)
    app.on_shutdown.append(shutdown)

    # Binds our Socket.IO server to our Web App instance
    sio.attach(app)

    # We bind our aiohttp endpoint to our app router
    app.router.add_get('/', index_page_handler)

    cors = aiohttp_cors.setup(app)

    for resource in app.router.resources():
        # Because socket.io already adds cors, if you don't skip socket.io, you get error saying, you've done this already.
        if resource.raw_match("/socket.io/"):
            continue

        cors.add(resource, {'*': aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})

    runner = web.AppRunner(app)
    logging.info("aiohttp_init - exit")
    return runner

#
# threads
#

def web_server(runner):
    '''
    Start the web server

    :runner web.AppRunner
    :return None
    '''
    global server_address
    global server_port
    global Webserver_loop

    logging.info("web_server thread - entry")
    Webserver_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(Webserver_loop)

    # server setup
    Webserver_loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, server_address, server_port)
    Webserver_loop.run_until_complete(site.start())
    logging.info("web_server - thread starting run loop")

    # start the server, run until explicitly stopped
    Webserver_loop.run_forever()

    # once stop is called, we run the cleanup task
    Webserver_loop.run_until_complete(runner.cleanup())

    logging.info("web_server thread - exit")


def stdin_reader():
    '''
    Read from STDIN until CTRL-D

    :id int The thread id
    :return None
    '''
    global Verbose

    logging.info("stdin_reader thread - entry")

    for line in sys.stdin:
        logging.info("STDIN: {}".format(line.rstrip()))

    shutdown_server()

    logging.info("stdin_reader thread - exit")

#
# async handlers
#

@sio.on('connect', namespace='/')
def connect_handler(sid, environ):
    '''
    Connection handler

    :sid hash connection
    :environ dictionary
    :return None
    '''

    logging.info("connect(" + sid + ") - entry")

    #print("{}".format(environ))

    if sid in app['connections']:
        print("Error ----------- conn exists")
        logging.info("Error ----------- conn exists")
    else:
        conn = {
            "id": sid,
            "environ": environ,
            "last_seen": time.time(),
            "connected_on": time.time(),
            "last_message": ""
        }

    app['connections'][sid] = conn

    logging.info("connect - exit")


@sio.on('disconnect', namespace='/')
def disconnect_handler(sid):
    '''
    Disconnect handler

    :sid hash connection
    :return None
    '''
    logging.info("disconnect(" + sid + ") - entry")

    if sid in app['connections']:
        app['connections'].pop(sid, None)
    else:
        logging.info("disconnect - Error: Unknown connection: " + sid)

    logging.info("disconnect - exit")


async def startup(app):
    '''
    Web server startup

    :app object web.Application
    :return None
    '''
    logging.info("web server startup - entry/exit")


async def cleanup(app):
    '''
    Web server cleanup

    :app object web.Application
    :return None
    '''
    logging.info("web server cleanup: entry/exit")


async def shutdown(app):
    '''
    Web server shutdown

    :app object web.Application
    :return None
    '''
    logging.info("web server shutdown: entry/exit")


# we can define aiohttp endpoints just as we normally would with no change
async def index_page_handler(request):
    with open('index.2.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@sio.on('short_request')
async def handle_short_request(sid, data):
    logging.info("handle_short_request(" + sid + ") - entry")
    await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"short_request"}', room=sid)
    logging.info("handle_short_request - exit")
    return "short_request ack"


@sio.on('long_request')
async def handle_long_request(sid, data):
    logging.info("handle_long_request(" + sid + ") - entry")

    loop = asyncio.get_event_loop()

    # will block until there are threads available
    task = loop.run_in_executor(tp_executor, block_for, long_request_delay) # task block for n seconds

    completed, pending = await asyncio.wait([task])

    results = [t.result() for t in completed]

    logging.info('handle_long_request - results: {!r}'.format(results))

    await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"long_request"}', room=sid)

    logging.info("handle_long_request - exit")

    return "long_request ack"


@sio.on('shutdown')
async def handle_shutdown_request(sid, data):
    logging.info("handle_shutdown_request(" + sid + ") - entry")
    await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"shutdown"}', room=sid)
    shutdown_server()
    logging.info("handle_shutdown_request - exit")
    return "shutdown_request ack"


@sio.on('connections')
async def handle_connections_request(sid, data):
    logging.info("handle_connections_request(" + sid + ") - entry")
    conn_list = json.dumps(list(app['connections'].keys()));
    await sio.emit("message", '{"response":' + conn_list + ', "response-text":"ok", "response-code":200, "request":"connections"}', room=sid)
    logging.info("handle_connections_request - exit")
    return "connections_ack"


#
# main
#
if __name__ == "__main__":

    #logging.basicConfig(format="%(asctime)s: %(message)s", filename='asyncwebserver.2.log', filemode='w',  level=logging.DEBUG, datefmt="%H:%M:%S")

    print("UI on http://{}:{}, logging to {}".format(server_address, server_port, logfile))

    logging.info("main - entry")

    # start the STDIN reader as a daemon so that it goes away when main exits
    t_stdin_reader = threading.Thread(target=stdin_reader, args=(), daemon=True)

    # the server isn't a daemon because it needs a clean shutdown
    t_webserver = threading.Thread(target=web_server, args=(aiohttp_init(),), daemon=False)

    logging.info("main - starting stdin reader")

    t_stdin_reader.start()

    logging.info("main - starting web server")

    t_webserver.start()
    t_webserver.join() # wait for web server thread to exit

    print("Goodbye", flush=True)

    logging.info("main - exit")

# end file
