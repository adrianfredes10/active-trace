"""Worker placeholder — la cola real se define en ADR-003."""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("Worker placeholder started (no-op loop)")
    while True:
        await asyncio.sleep(60)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":
    main()
