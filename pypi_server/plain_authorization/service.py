from aiohttp import web
from aiomisc.service.aiohttp import AIOHTTPService
from patio import AbstractBroker


class HTTPService(AIOHTTPService):
    __dependencies__ = ("patio_broker",)

    patio_broker: AbstractBroker

    async def create_application(self) -> web.Application:
        app = web.Application()
        app["broker"] = self.patio_broker
        return app
