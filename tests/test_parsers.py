import unittest

from laugh_loop.models import Joke, JokeProvider
from laugh_loop.parsers import JokeParser


class JokeParserTests(unittest.TestCase):
    def test_parses_single_joke(self) -> None:
        self.assertEqual(
            JokeParser.parse_jokeapi(
                {"error": False, "type": "single", "joke": "A short joke."}
            ),
            Joke(provider=JokeProvider.JOKEAPI, text="A short joke."),
        )

    def test_parses_two_part_joke(self) -> None:
        self.assertEqual(
            JokeParser.parse_jokeapi(
                {
                    "error": False,
                    "type": "twopart",
                    "setup": "Why did the scarecrow win an award?",
                    "delivery": "He was outstanding in his field.",
                }
            ),
            Joke(
                provider=JokeProvider.JOKEAPI,
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
                JokeParser.parse_jokeapi(response)

    def test_parses_dad_joke(self) -> None:
        self.assertEqual(
            JokeParser.parse_dad_joke({"joke": "A dad joke."}),
            Joke(provider=JokeProvider.ICANHAZDADJOKE, text="A dad joke."),
        )

    def test_rejects_invalid_dad_joke(self) -> None:
        with self.assertRaises(ValueError):
            JokeParser.parse_dad_joke({"joke": ""})


if __name__ == "__main__":
    unittest.main()
