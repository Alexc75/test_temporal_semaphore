from collections.abc import Mapping
from typing import Any

import httpx
from temporalio import activity

from .models import Joke

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


def _parse_jokeapi_response(payload: Mapping[str, Any]) -> Joke:
    if not isinstance(payload, Mapping):
        raise ValueError("JokeAPI response must be a JSON object")

    if payload.get("error") is not False:
        raise ValueError("JokeAPI returned an error response")

    joke_type = payload.get("type")
    if joke_type == "single":
        text = payload.get("joke")
    elif joke_type == "twopart":
        setup = payload.get("setup")
        delivery = payload.get("delivery")
        if isinstance(setup, str) and isinstance(delivery, str):
            if not setup.strip() or not delivery.strip():
                raise ValueError("JokeAPI response did not contain a valid joke")
            text = f"{setup.strip()}\n{delivery.strip()}"
        else:
            text = None
    else:
        text = None

    if not isinstance(text, str) or not text.strip():
        raise ValueError("JokeAPI response did not contain a valid joke")
    return Joke(provider="JokeAPI", text=text)


def _parse_dad_joke_response(payload: Mapping[str, Any]) -> Joke:
    if not isinstance(payload, Mapping):
        raise ValueError("icanhazdadjoke response must be a JSON object")

    text = payload.get("joke")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("icanhazdadjoke response did not contain a valid joke")
    return Joke(provider="icanhazdadjoke", text=text.strip())


class JokeActivities:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    @activity.defn(name="fetch_jokeapi_joke")
    async def fetch_jokeapi_joke(self) -> Joke:
        activity.logger.info("Fetching a joke from JokeAPI")
        try:
            payload = await _get_json(self.client, JOKEAPI_URL)
            joke = _parse_jokeapi_response(payload)
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
            joke = _parse_dad_joke_response(payload)
        except (httpx.HTTPError, ValueError):
            activity.logger.exception("Failed to fetch a joke from icanhazdadjoke")
            raise
        activity.logger.info("Successfully fetched a joke from icanhazdadjoke")
        return joke
