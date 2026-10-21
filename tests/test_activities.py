import unittest

import httpx
from temporalio.testing import ActivityEnvironment

from laugh_loop.activities import JokeActivities
from laugh_loop.models import Joke, JokeProvider


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

        self.assertEqual(
            joke, Joke(provider=JokeProvider.JOKEAPI, text="A short joke.")
        )

    async def test_fetch_dad_joke(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["accept"], "application/json")
            return httpx.Response(200, json={"joke": "A dad joke."})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            activities = JokeActivities(client)
            joke = await ActivityEnvironment().run(activities.fetch_dad_joke)

        self.assertEqual(
            joke, Joke(provider=JokeProvider.ICANHAZDADJOKE, text="A dad joke.")
        )


if __name__ == "__main__":
    unittest.main()
