from app.openalex import OpenAlexClient
from tests.conftest import fixture_transport


class CountingTransport:
    def __init__(self):
        self.calls = 0
        self._inner = fixture_transport()

    async def handle_async_request(self, request):
        self.calls += 1
        return await self._inner.handle_async_request(request)

    async def aclose(self):
        await self._inner.aclose()


async def test_disk_cache_avoids_repeat_requests(tmp_path):
    counting = CountingTransport()
    client = OpenAlexClient(transport=counting, cache_dir=tmp_path)
    first = await client.search_works("retrieval augmented generation", 10)
    second = await client.search_works("retrieval augmented generation", 10)
    await client.aclose()
    assert counting.calls == 1
    assert first == second
