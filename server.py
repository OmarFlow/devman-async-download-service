import os
import asyncio
import logging
import argparse
from sys import stdout
from functools import partial

import aiofiles
from aiohttp import web

from constans import DEFAULT_PHOTO_FOLDER_PATH, CHUNK_SIZE


logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(stdout)
logger.addHandler(consoleHandler)


async def archive(request, download_logging=None, delay=None, photo_folder_path=None):
    response = web.StreamResponse()
    response.enable_chunked_encoding()
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment'
    response.headers['Transfer-Encoding'] = 'chunked'

    archive_hash = request.match_info['archive_hash']

    full_path = os.path.join(os.getcwd(), photo_folder_path, archive_hash)

    if not os.path.exists(full_path):
        raise web.HTTPNotFound()
    await response.prepare(request)

    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-',  '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=f'{photo_folder_path}/{archive_hash}/'
    )

    try:
        while not proc.stdout.at_eof():
            _stdout = await proc.stdout.read(CHUNK_SIZE)
            if download_logging:
                logger.info('Sending archive chunk ...')
            await response.write(_stdout)
            if delay:
                await asyncio.sleep(2)
        await response.write_eof()

    except ConnectionResetError:
        logger.debug('Download was interrupted')
    except Exception as e:
        logger.debug(f'It was faced an error: {str(e)}')
    else:
        logger.info('Succes')
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.communicate()

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--logging", help="enable logging", type=str)
    parser.add_argument("--delay", help="enable delay while downloading", type=str)
    parser.add_argument("--photo_folder_path", help="path to photo folder", type=str)
    args = parser.parse_args()

    download_logging = False
    if args.logging == "true":
        download_logging = True

    delay = False
    if args.delay == "true":
        delay = True

    photo_folder_path = DEFAULT_PHOTO_FOLDER_PATH
    if args.photo_folder_path:
        photo_folder_path = args.photo_folder_path

    p_archive = partial(archive, download_logging=download_logging, delay=delay, photo_folder_path=photo_folder_path)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', p_archive),
    ])
    web.run_app(app)
