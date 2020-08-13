# давай вот щас не начинай, работает, а больше мне ничего не нужно
import asyncio
import aiohttp
from .exceptions import VkResponseException, NetworkError, TokenInvalid, TooManyRequests
from .methods import Messages
from .request import post

# from wtflog import warden
# logger = warden.get_boy('VK API')
from .printer import Printer
logger = Printer()

class VkApi:
    url: str = 'https://api.vk.com/method/'
    query: str
    excepts: bool

    messages = Messages

    def __init__(self, access_token: str, excepts: bool = False, version: str = "5.110"):
        'Eсли excepts == True, ошибки ВК будут генерировать исключение VkResponseException'
        self.query = f'?v={version}&access_token={access_token}&lang=ru'
        self.excepts = excepts


    async def __call__(self, method, **kwargs):
        logger.debug(f'URL = "{self.url}{method}{self.query}" Data = {kwargs}')
        resp_body = await post(f'{self.url}{method}{self.query}', kwargs, self.excepts)
        if 'response' in resp_body.keys():
            logger.info(f"Запрос {method} выполнен")
            return resp_body['response']
        elif 'error' in resp_body.keys():
            logger.warning(f"Запрос {method} не выполнен: {resp_body['error']}")
            if self.excepts:
                if resp_body['error']['error_code'] == 5:
                    raise TokenInvalid
                if resp_body['error']['error_code'] == 6:
                    raise TooManyRequests(kwargs)
                else:
                    raise VkResponseException(resp_body["error"])
        return resp_body


    async def msg_op(self, mode: int, peer_id: int = 0, text: str = '',
               msg_id: int = 0, delete_delay: float = 0, **kwargs):
        '''`mode` 1 - отправка, 2 - редактирование, 3 - удаление, 4 - удаление только для себя\n
        Если указан параметр `delete_delay` - сообщение удалится через указанное количество секунд'''
        if mode == 4:
            mode = 3
            dfa = 0
        else: dfa = 1

        mode = ['messages.send', 'messages.edit', 'messages.delete'][mode - 1]
        
        response = await self(mode, peer_id = peer_id, message = text,
        message_id = msg_id, delete_for_all = dfa, random_id = 0, **kwargs)
        if delete_delay:
            await asyncio.sleep(delete_delay)
            if mode == 1: msg_id = response
            await self('messages.delete', message_id = msg_id, delete_for_all = 1)
        return response
            

    async def exe(self, code, alt_token = ''):
        '''Метод execute\n
        Если указан `alt_token`, запрос будет отправлен с указанным токеном'''
        if alt_token:
            return await VkApi(alt_token, self.excepts)('execute', code = code)
        else:
            return await self('execute', code = code)