import asyncio
import logging
import uuid

from temporalio.client import Client

from .settings import (
    TEMPORAL_ADDRESS,
    TEMPORAL_NAMESPACE,
    TEMPORAL_TASK_QUEUE,
)
from .workflows import LaughWorkflow

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info(
        "Connecting to Temporal at %s (namespace=%s)",
        TEMPORAL_ADDRESS,
        TEMPORAL_NAMESPACE,
    )
    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
    )
    workflow_id = f"laugh-loop-{uuid.uuid4()}"
    handle = await client.start_workflow(
        LaughWorkflow.run,
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE,
    )
    logger.info(
        "Started workflow %s on task queue %s; waiting for results",
        handle.id,
        TEMPORAL_TASK_QUEUE,
    )
    jokes = await handle.result()
    logger.info("Workflow %s completed with %d jokes", handle.id, len(jokes))

    print("Here are today's laughs:\n")
    for joke in jokes:
        print(f"[{joke.provider}] {joke.text}\n")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
