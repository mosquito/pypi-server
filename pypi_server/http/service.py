from aiohttp import web
from aiomisc.service.aiohttp import AIOHTTPService


class HTTPService(AIOHTTPService):
    async def create_application(self) -> web.Application:
        app = web.Application()
        return app
