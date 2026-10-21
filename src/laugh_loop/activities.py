from collections.abc import Mapping
from typing import Any

import httpx
from temporalio import activity

from .models import Joke
from .parsers import JokeParser

JOKEAPI_URL = "https://v2.jokeapi.dev/joke/Any?safe-mode"
DAD_JOKE_URL = "https://icanhazdadjoke.com/"
HTTP_TIMEOUT_SECONDS = 5.0


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected a JSON object from {url}")
    return dict(payload)


class JokeActivities:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    @activity.defn(name="fetch_jokeapi_joke")
    async def fetch_jokeapi_joke(self) -> Joke:
        activity.logger.info("Fetching a joke from JokeAPI")
        try:
            payload = await _get_json(self.client, JOKEAPI_URL)
            joke = JokeParser.parse_jokeapi(payload)
        except (httpx.HTTPError, ValueError):
            activity.logger.exception("Failed to fetch a joke from JokeAPI")
            raise
        activity.logger.info("Successfully fetched a joke from JokeAPI")
        return joke

    @activity.defn(name="fetch_dad_joke")
    async def fetch_dad_joke(self) -> Joke:
        activity.logger.info("Fetching a joke from icanhazdadjoke")
        try:
            payload = await _get_json(
                self.client,
                DAD_JOKE_URL,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "LaughLoop/0.1.0 (local Temporal demo)",
                },
            )
            joke = JokeParser.parse_dad_joke(payload)
        except (httpx.HTTPError, ValueError):
            activity.logger.exception("Failed to fetch a joke from icanhazdadjoke")
            raise
        activity.logger.info("Successfully fetched a joke from icanhazdadjoke")
        return joke
