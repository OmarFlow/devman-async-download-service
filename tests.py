from aiohttp import web

from server import handle_index_page, archive


async def test_index(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', handle_index_page)
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'Микросервис для скачивания файлов' in text


async def test_download(aiohttp_client):
    app = web.Application()
    app.router.add_get('/archive/{archive_hash}/', archive)
    client = await aiohttp_client(app)
    resp = await client.get('/archive/7kna/')
    assert resp.status == 200
    body = await resp.content.read()
    assert type(body) == bytes
