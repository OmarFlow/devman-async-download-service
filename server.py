import os
import asyncio
import logging
import argparse
from sys import stdout

from aiohttp import web
import aiofiles

from constans import DEFAULT_PHOTO_FOLDER_PATH, CHUNK_SIZE


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(stdout)
logger.addHandler(consoleHandler)


async def archive(request):
    response = web.StreamResponse()
    await response.prepare(request)

    is_logging = os.getenv("LOGGING")
    is_delay = os.getenv("DELAY")
    is_env_photo_path = os.getenv("PHOTO_PATH")

    archive_hash = request.match_info.get('archive_hash')
    if env_photo_folder_path := is_env_photo_path:
        photo_folder_path = env_photo_folder_path
    else:
        photo_folder_path = DEFAULT_PHOTO_FOLDER_PATH
    full_path = os.path.join(os.getcwd(), photo_folder_path, archive_hash)

    if not os.path.exists(full_path):
        raise web.HTTPNotFound()

    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-',  '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=f'{photo_folder_path}/{archive_hash}/'
    )

    try:
        while not proc.stdout.at_eof():
            _stdout = await proc.stdout.read(CHUNK_SIZE)

            if is_logging:
                logger.info('Sending archive chunk ...')
            await response.write(_stdout)
            if is_delay:
                await asyncio.sleep(2)

    except ConnectionResetError:
        logger.debug('Download was interrupted')
    except Exception as e:
        logger.debug(f'It was faced an error: {str(e)}')
    else:
        logger.info('Succes')
    finally:
        try:
            proc.kill()
            await proc.communicate()
        except ProcessLookupError:
            ...

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--logging", help="enable logging", type=str)
    parser.add_argument("--delay", help="enable delay while downloading", type=str)
    parser.add_argument("--photo_path", help="path to photo folder", type=str)
    args = parser.parse_args()

    if args.logging == "true":
        os.environ['LOGGING'] = "1"

    if args.delay == "true":
        os.environ['DELAY'] = "1"

    if args.photo_path:
        os.environ['PHOTO_PATH'] = args.photo_path

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
