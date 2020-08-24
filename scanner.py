from aiohttp import web
import logging
import logging.handlers
import json
import asyncio


def add_log_handler(logger, log_level=logging.DEBUG):
    # create syslog logger handler
    sh = logging.handlers.SysLogHandler(address='/dev/log')
    sh.setLevel(log_level)
    sf = logging.Formatter('%(name)s: %(message)s')
    sh.setFormatter(sf)
    logger.addHandler(sh)


def catch_exception(func):
    async def decorated_function(ip, port, scan_loop):
        try:
            await func(ip, port, scan_loop)
            return [{"port": str(port), "state": "open"}]
        except asyncio.TimeoutError:
            return [{"port": str(port), "state": "close"}]
    return decorated_function


@catch_exception
async def check_port(ip, port, scan_loop):
    conn = asyncio.open_connection(ip, port, loop=scan_loop)
    await asyncio.wait_for(conn, timeout=3)


async def run(ip, begin_port, end_port, scan_loop):
    tasks = [asyncio.ensure_future(check_port(ip, p, scan_loop)) for p in range(begin_port, end_port)]
    responses = await asyncio.gather(*tasks)
    return responses


async def handle(request):
    ip = request.match_info.get('ip')
    begin_port = int(request.match_info.get('begin_port'))
    end_port = int(request.match_info.get('end_port'))

    loop = asyncio.get_event_loop()
    results = await asyncio.ensure_future(run(ip, begin_port, end_port, loop))
    print(results)
    response_obj = {'data': results}

    return web.Response(text=json.dumps(response_obj), status=200)


app = web.Application()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('scanner')
add_log_handler(logger)
app.router.add_get('/scan/{ip}/{begin_port}/{end_port}', handle)

if __name__ == '__main__':
    web.run_app(app, access_log=logger)
