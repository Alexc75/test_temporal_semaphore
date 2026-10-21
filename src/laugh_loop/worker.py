import asyncio
import logging

import httpx
from temporalio.client import Client
from temporalio.worker import Worker

from .activities import HTTP_TIMEOUT_SECONDS, JokeActivities
from .settings import (
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
    TEMPORAL_TASK_QUEUE,
)
from .workflows import LaughWorkflow

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    logger.info(
        "Connecting to Temporal at %s (namespace=%s)",
        TEMPORAL_ADDRESS,
        TEMPORAL_NAMESPACE,
    )
    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
    )
    logger.info("Connected to Temporal")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as http_client:
        activities = JokeActivities(http_client)
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            workflows=[LaughWorkflow],
            activities=[
                activities.fetch_jokeapi_joke,
                activities.fetch_dad_joke,
            ],
        )
        logger.info("Starting worker on task queue %s", TEMPORAL_TASK_QUEUE)
        await worker.run()
        logger.info("Worker stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
