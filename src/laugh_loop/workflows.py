import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import JokeActivities
    from .models import Joke


@workflow.defn
class LaughWorkflow:
    @workflow.run
    async def run(self) -> list[Joke]:
        workflow.logger.info("Starting LaughWorkflow; fetching jokes in parallel")
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=5),
            maximum_attempts=3,
        )
        results = await asyncio.gather(
            workflow.execute_activity_method(
                JokeActivities.fetch_jokeapi_joke,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_policy,
            ),
            workflow.execute_activity_method(
                JokeActivities.fetch_dad_joke,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_policy,
            ),
        )
        workflow.logger.info("LaughWorkflow completed; fetched %d jokes", len(results))
        return list(results)
