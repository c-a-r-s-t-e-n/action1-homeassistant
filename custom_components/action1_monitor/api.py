"""Read-only Action1 API 3.0 client. Never log credentials or response bodies."""
import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from aiohttp import ClientError

ALLOWED_HOSTS = frozenset({
    "app.action1.com", "app.eu.action1.com", "app.na-2.action1.com",
    "app.au.action1.com", "app.uk.action1.com",
})


class Action1Error(Exception):
    """Public-safe API error."""


def validate_origin(origin):
    parts = urlsplit(origin)
    if (parts.scheme != "https"
            or parts.hostname not in ALLOWED_HOSTS
            or parts.port not in (None, 443)
            or parts.username or parts.password
            or parts.path.strip("/") or parts.query or parts.fragment):
        raise ValueError("Unsupported Action1 API region URL")
    return origin.rstrip("/")


def page_items(document):
    if isinstance(document, list):
        return document
    if isinstance(document, dict):
        items = document.get("items")
        if isinstance(items, list):
            return items
    return []


class Action1Client:
    def __init__(self, session, origin, client_id, client_secret):
        self.session = session
        self.origin = validate_origin(origin)
        self.id = client_id
        self.secret = client_secret
        self.token = None
        self.expiry = datetime.min.replace(tzinfo=timezone.utc)
        self._pace = asyncio.Lock()
        self._last_call = 0.0

    async def _login(self):
        try:
            async with self.session.post(
                f"{self.origin}/api/3.0/oauth2/token",
                data={"client_id": self.id, "client_secret": self.secret},
                timeout=25,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as exc:
            raise Action1Error("Action1 authentication failed") from exc
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not token:
            raise Action1Error("Action1 token missing")
        self.token = token
        seconds = max(60, int(payload.get("expires_in", 3600)) - 120)
        self.expiry = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    async def get(self, path, params=None):
        """GET on fixed API origin, with spacing and retry for rate limits."""
        if not path.startswith("/") or path.startswith("//") or "?" in path or "#" in path:
            raise Action1Error("Invalid resource path")
        if not self.token or datetime.now(timezone.utc) >= self.expiry:
            await self._login()
        for attempt in range(3):
            async with self._pace:
                loop = asyncio.get_running_loop()
                remaining = 2.25 - (loop.time() - self._last_call)
                if remaining > 0:
                    await asyncio.sleep(remaining)
                self._last_call = loop.time()
                try:
                    async with self.session.get(
                        f"{self.origin}/api/3.0{path}",
                        params=params,
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=40,
                    ) as response:
                        if response.status == 401 and attempt == 0:
                            await self._login()
                            continue
                        if response.status == 429 and attempt < 2:
                            await asyncio.sleep(12 * (attempt + 1))
                            continue
                        response.raise_for_status()
                        return await response.json(content_type=None)
                except (ClientError, TimeoutError, ValueError) as exc:
                    raise Action1Error(
                        f"Action1 GET failed: {path.rsplit('/', 1)[-1]}"
                    ) from exc
        raise Action1Error("Action1 request retry limit")

    async def pages(self, path, params=None, max_records=5000):
        """Follow ResultPage offsets; never request arbitrary API next_page URLs."""
        records = []
        offset = 0
        step = 100
        for _ in range(100):
            query = dict(params or {})
            query.update({"from": offset, "limit": step})
            document = await self.get(path, query)
            if isinstance(document, list):
                return document[:max_records]
            if not isinstance(document, dict):
                raise Action1Error("Unexpected Action1 collection shape")
            batch = page_items(document)
            records.extend(batch[:max(0, max_records - len(records))])
            total = document.get("total_items")
            try:
                total = int(total) if total is not None else None
            except (ValueError, TypeError):
                total = None
            if (len(records) >= max_records or not batch
                    or (total is not None and len(records) >= total)
                    or (total is None and len(batch) < step
                        and not document.get("next_page"))):
                break
            offset += len(batch)
        return records
