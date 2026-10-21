from dataclasses import dataclass
from enum import StrEnum


class JokeProvider(StrEnum):
    JOKEAPI = "JokeAPI"
    ICANHAZDADJOKE = "icanhazdadjoke"


@dataclass
class Joke:
    provider: JokeProvider
    text: str
