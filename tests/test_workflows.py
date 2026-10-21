import unittest
import uuid

from temporalio import activity
from temporalio.client import WorkflowFailureError
from temporalio.exceptions import ActivityError, ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from laugh_loop.models import Joke, JokeProvider
from laugh_loop.workflows import LaughWorkflow

TASK_QUEUE = "laugh-loop-test"
JOKEAPI_JOKE = Joke(provider=JokeProvider.JOKEAPI, text="A short joke.")
DAD_JOKE = Joke(provider=JokeProvider.ICANHAZDADJOKE, text="A dad joke.")


@activity.defn(name="fetch_jokeapi_joke")
async def fetch_jokeapi_joke() -> Joke:
    return JOKEAPI_JOKE


@activity.defn(name="fetch_dad_joke")
async def fetch_dad_joke() -> Joke:
    return DAD_JOKE


class LaughWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # The time-skipping server makes retry backoff instant.
        self.env = await WorkflowEnvironment.start_time_skipping()

    async def asyncTearDown(self) -> None:
        await self.env.shutdown()

    async def _run_workflow(self, *activities) -> list[Joke]:
        async with Worker(
            self.env.client,
            task_queue=TASK_QUEUE,
            workflows=[LaughWorkflow],
            activities=list(activities),
        ):
            return await self.env.client.execute_workflow(
                LaughWorkflow.run,
                id=f"laugh-loop-test-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

    async def test_returns_jokes_from_both_providers(self) -> None:
        jokes = await self._run_workflow(fetch_jokeapi_joke, fetch_dad_joke)

        self.assertEqual(jokes, [JOKEAPI_JOKE, DAD_JOKE])

    async def test_retries_failed_activity(self) -> None:
        attempts = 0

        @activity.defn(name="fetch_dad_joke")
        async def flaky_dad_joke() -> Joke:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ApplicationError("icanhazdadjoke is unavailable")
            return DAD_JOKE

        # Capture the worker's failure logs so expected tracebacks don't clutter output.
        with self.assertLogs("temporalio.activity", "WARNING") as logs:
            jokes = await self._run_workflow(fetch_jokeapi_joke, flaky_dad_joke)

        self.assertEqual(len(logs.records), 2)
        self.assertEqual(jokes, [JOKEAPI_JOKE, DAD_JOKE])
        self.assertEqual(attempts, 3)

    async def test_fails_after_max_attempts(self) -> None:
        attempts = 0

        @activity.defn(name="fetch_dad_joke")
        async def failing_dad_joke() -> Joke:
            nonlocal attempts
            attempts += 1
            raise ApplicationError("icanhazdadjoke is unavailable")

        with (
            self.assertLogs("temporalio.activity", "WARNING") as logs,
            self.assertRaises(WorkflowFailureError) as raised,
        ):
            await self._run_workflow(fetch_jokeapi_joke, failing_dad_joke)

        self.assertEqual(len(logs.records), 3)
        self.assertIsInstance(raised.exception.cause, ActivityError)
        self.assertEqual(attempts, 3)


if __name__ == "__main__":
    unittest.main()
