from dataclasses import dataclass


@dataclass
class Joke:
    provider: str
    text: str
