#!/usr/bin/env python3.6
#
# Web server with websockets
#
# Logs to asyncwebserver.log
#

import sys
import socketio
import asyncio
import logging
import threading
import aiohttp_cors
import time

from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

# creates a new Async Socket IO Server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*') # , async_handlers=True will prevent queueing of messages from a single client

logfile = 'asyncwebserver.2.log'

logging.basicConfig(
    format="%(asctime)s: %(message)s",
    filename=logfile,
    filemode='w',
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

server_address = "localhost"
server_port = "8080"

Webserver_loop = None

def block_for(secs):
    '''

    '''
    logging.info("block_for - entry({})".format(secs))

    time.sleep(secs)

    #t0 = time.time()
    #x = 0
    #while time.time() < t0 + secs:
    #    x = x + 1

    logging.info("block_for - exit")

    return "block_for done"

def aiohttp_server():
    '''
    Create a web server

    :return None
    '''
    global sio

    logging.info("aiohttp_server - entry")

    # Creates a new Aiohttp Web Application
    app = web.Application()

    # Binds our Socket.IO server to our Web App instance
    sio.attach(app)

    tp_executor = ThreadPoolExecutor(max_workers = 2)

    # we can define aiohttp endpoints just as we normally would with no change
    async def index_page_handler(request):
        with open('index.2.html') as f:
            return web.Response(text=f.read(), content_type='text/html')

    @sio.on('short_request')
    async def handle_short_request(sid, data):
        logging.info("handle_short_request - entry")
        await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"short_request"}', room=sid)
        logging.info("handle_short_request - exit")
        return "short_request ack"

    @sio.on('long_request')
    async def handle_long_request(sid, data):
        logging.info("handle_long_request - entry")

        logging.info("handle_long_request - data:" + str(data))

        if not data:
            return "long_request ack - no data"

        logging.info("handle_long_request - before run_in_executor".format())

        loop = asyncio.get_event_loop()

        # delay, e.g block_for(n)
        n = 10

        # will block until there are threads available
        task = loop.run_in_executor(tp_executor, block_for, n) # task block for n seconds

        completed, pending = await asyncio.wait([task])

        results = [t.result() for t in completed]

        logging.info('results: {!r}'.format(results))

        logging.info("block_for - before emit")

        await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"long_request"}', room=sid)

        logging.info("handle_long_request - exit")

        return "long_request ack"

    @sio.on('shutdown')
    async def handle_shutdown_request(sid, data):
        logging.info("handle_shutdown_request - entry")
        await sio.emit("message", '{"response":"ok", "response-text":"ok", "response-code":200, "request":"shutdown"}', room=sid)
        print("Goodbye", flush=True)
        shutdown_server()
        logging.info("handle_shutdown_request - exit")
        return "shutdown_request ack"

    # We bind our aiohttp endpoint to our app router
    app.router.add_get('/', index_page_handler)

    cors = aiohttp_cors.setup(app)

    for resource in app.router.resources():
        # Because socket.io already adds cors, if you don't skip socket.io, you get error saying, you've done this already.
        if resource.raw_match("/socket.io/"):
            continue

        cors.add(resource, {'*': aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})

    runner = web.AppRunner(app)
    logging.info("aiohttp_server - exit")
    return runner


def run_server(runner):
    '''
    Start the web server

    :return None
    '''
    global server_address
    global server_port
    global Webserver_loop

    logging.info("run_server - entry")
    Webserver_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(Webserver_loop)

    # server setup
    Webserver_loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, server_address, server_port)
    Webserver_loop.run_until_complete(site.start())
    logging.info("run_server - starting run loop")

    # start the server, run until explicitly stopped
    Webserver_loop.run_forever()

    # once stop is called, we run the cleanup task
    Webserver_loop.run_until_complete(runner.cleanup())

    logging.info("run_server - exit")


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

    #logging.basicConfig(format="%(asctime)s: %(message)s", filename='asyncwebserver.2.log', filemode='w',  level=logging.DEBUG, datefmt="%H:%M:%S")

    print("UI on http://{}:{}, logging to {}".format(server_address, server_port, logfile))

    logging.info("main - entry")

    logging.info("main - creating threads ...")

    # the server isn't a daemon because it needs a clean shutdown
    t_webserver = threading.Thread(target=run_server, args=(aiohttp_server(),), daemon=False)

    logging.info("main - creating threads ... done.")

    logging.info("main - starting threads ...")

    t_webserver.start()

    logging.info("main - starting threads ... done.")

    logging.info("main - waiting for web server thread to finish ...")

    t_webserver.join()

    logging.info("main - waiting for web server thread to finish ... done.")

    logging.info("main - exit")

# end file
