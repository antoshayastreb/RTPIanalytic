from aiohttp import (
    ClientSession,
    ClientResponse, 
    ClientTimeout
)
from aiohttp.hdrs import METH_GET
from scheduler_service.exceptions import Unsuccessful
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_random_exponential, 
    retry_if_not_exception_type
)
from typing import Optional
import logging

from .config import settings

client_get_count = ClientTimeout(total = int(settings.CLIENT_TIMEOUT_GET_COUNT))
client_get_content = ClientTimeout(total = int(settings.CLIENT_TIMEOUT_GET_CONTENT))

base_headers = {
    'Authorization': f'Bearer {settings.RTPI_API_TOKEN}',
    'Content-Type': 'application/json',
    'Range-Unit': 'items'
}

count_headers = {
    'Range' : '0-1',
    'Prefer' : 'count=exact'
}

logger = logging.getLogger(__name__)

class ScraperSession(ClientSession):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            base_url=settings.RTPI_REQUEST_BASEURL,
            headers=base_headers,
            timeout=client_get_count,
            *args, 
            **kwargs
        )

    async def get_count(self, url, **kwargs) -> int:
        try:
            response = None
            response = await self._request(
                    METH_GET,
                    url,
                    expect_json=True,
                    expected_mime_type="application/json",
                    headers=count_headers,
                    **kwargs,
                )
            assert response.status // 100 == 2
            range = response.headers.get('content-Range')
            return (int)((range.split('/'))[1])
        except (Exception, AssertionError) as ex:
            if isinstance(ex, AssertionError):
                mes = await response.json()
                raise Unsuccessful(mes)
            else:
                raise ex

    async def get_json(self, url: str, **kwargs) -> dict:
        return await (
            await self._request(
                METH_GET,
                url,
                expect_json=True,
                expected_mime_type="application/json",
                **kwargs,
            )
        ).json()


    @retry(
        stop=stop_after_attempt(int(settings.CLIENT_RETRY_ATTEMPTS)),
        wait=wait_random_exponential(multiplier=1, max=60),
        retry=retry_if_not_exception_type(Unsuccessful)
    )
    async def _request(
        self,
        *args,
        expect_json: bool = False,
        expected_mime_type: Optional[str] = None,
        **kwargs
    ) -> ClientResponse:
        try:
            response = await super()._request(*args, **kwargs)

            if expected_mime_type:
                content_type = response.headers.get("content-type", "")
                success = expected_mime_type.lower() in content_type.lower()

                if not success:
                    raise Unsuccessful(
                        f"MIME type не соответствует заявленному. (Заявлен '{expected_mime_type}', получен {content_type})."
                    )

            if expect_json:
                try:
                    await response.json()
                except Exception as e:
                    raise Unsuccessful(f"Не удалось получить json: {e}")

            if not expect_json:
                if not response or not (await response.text()):
                    raise Unsuccessful(f"Пустой ответ")

            return response
        except TimeoutError as ex:
            logger.info(f"Время ожидания от сервера истекло")
            raise TimeoutError("Время ожидания от сервера истекло")
        # except Exception as ex:
        #     logger.error(f"Ошибка при выполнении запроса: {ex}")
        #     raise ex