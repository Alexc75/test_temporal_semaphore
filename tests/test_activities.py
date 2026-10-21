import unittest

import httpx
from temporalio.testing import ActivityEnvironment

from laugh_loop.activities import (
    JokeActivities,
    _parse_dad_joke_response,
    _parse_jokeapi_response,
)
from laugh_loop.models import Joke


class JokeParsingTests(unittest.TestCase):
    def test_parses_single_joke(self) -> None:
        self.assertEqual(
            _parse_jokeapi_response(
                {"error": False, "type": "single", "joke": "A short joke."}
            ),
            Joke(provider="JokeAPI", text="A short joke."),
        )

    def test_parses_two_part_joke(self) -> None:
        self.assertEqual(
            _parse_jokeapi_response(
                {
                    "error": False,
                    "type": "twopart",
                    "setup": "Why did the scarecrow win an award?",
                    "delivery": "He was outstanding in his field.",
                }
            ),
            Joke(
                provider="JokeAPI",
                text="Why did the scarecrow win an award?\n"
                "He was outstanding in his field.",
            ),
        )

    def test_rejects_jokeapi_error_and_invalid_shape(self) -> None:
        invalid_responses = (
            {"error": True},
            {"error": False, "type": "single", "joke": ""},
            {"error": False, "type": "unknown"},
            {"error": "false", "type": "single", "joke": "A short joke."},
            {"error": False, "type": "twopart", "setup": " ", "delivery": "A"},
            {"error": False, "type": "twopart", "setup": "A", "delivery": " "},
        )
        for response in invalid_responses:
            with self.subTest(response=response), self.assertRaises(ValueError):
                _parse_jokeapi_response(response)

    def test_parses_dad_joke(self) -> None:
        self.assertEqual(
            _parse_dad_joke_response({"joke": "A dad joke."}),
            Joke(provider="icanhazdadjoke", text="A dad joke."),
        )

    def test_rejects_invalid_dad_joke(self) -> None:
        with self.assertRaises(ValueError):
            _parse_dad_joke_response({"joke": ""})


class JokeActivityTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_jokeapi_joke(self) -> None:
        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "error": False,
                    "type": "single",
                    "joke": "A short joke.",
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            activities = JokeActivities(client)
            joke = await ActivityEnvironment().run(activities.fetch_jokeapi_joke)

        self.assertEqual(joke, Joke(provider="JokeAPI", text="A short joke."))

    async def test_fetch_dad_joke(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["accept"], "application/json")
            return httpx.Response(200, json={"joke": "A dad joke."})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            activities = JokeActivities(client)
            joke = await ActivityEnvironment().run(activities.fetch_dad_joke)

        self.assertEqual(joke, Joke(provider="icanhazdadjoke", text="A dad joke."))


if __name__ == "__main__":
    unittest.main()
