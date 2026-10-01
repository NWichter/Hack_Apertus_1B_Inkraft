"""Minimal OpenAI-compatible chat client (stdlib only) with retries."""

import json
import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


def redact(raw):
    """Error bodies may echo key identifiers; never store them."""
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    return re.sub(r"(api[_ ]?key[^:]*:\s*)[^\s.,]+", r"\1[redacted]", text, flags=re.I)


class Endpoint:
    def __init__(self, base_url, api_key, model):
        if not (base_url and model):
            raise SystemExit("endpoint needs a base URL and a model name")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.model = model

    @classmethod
    def from_env(cls, prefix="LLM", model=None):
        return cls(
            os.environ.get(f"{prefix}_BASE_URL"),
            os.environ.get(f"{prefix}_API_KEY"),
            model or os.environ.get(f"{prefix}_NAME"),
        )

    @property
    def host(self):
        return urlparse(self.base_url).netloc

    def chat(self, messages, retries=7, timeout=180, **params):
        body = json.dumps(
            {"model": self.model, "messages": messages, **params}
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        for attempt in range(retries):
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.loads(r.read())
                data["_latency_ms"] = int((time.time() - t0) * 1000)
                return data
            except urllib.error.HTTPError as e:
                if (
                    e.code not in (408, 409, 429, 500, 502, 503, 504)
                    or attempt == retries - 1
                ):
                    raise RuntimeError(f"HTTP {e.code}: {redact(e.read()[:300])!r}") from e
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == retries - 1:
                    raise
            time.sleep(min(60, 2 ** (attempt + 1)))
        raise RuntimeError("unreachable")
