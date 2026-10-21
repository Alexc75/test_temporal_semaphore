from collections.abc import Mapping
from typing import Any

from .models import Joke, JokeProvider


class JokeParser:
    """Validates joke API payloads and converts them to `Joke` objects."""

    @staticmethod
    def parse_jokeapi(payload: Mapping[str, Any]) -> Joke:
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
        return Joke(provider=JokeProvider.JOKEAPI, text=text)

    @staticmethod
    def parse_dad_joke(payload: Mapping[str, Any]) -> Joke:
        if not isinstance(payload, Mapping):
            raise ValueError("icanhazdadjoke response must be a JSON object")

        text = payload.get("joke")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("icanhazdadjoke response did not contain a valid joke")
        return Joke(provider=JokeProvider.ICANHAZDADJOKE, text=text.strip())
