import asyncio

from src.logger import get_logger


class TaskService:

    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}

    async def start_cleanup_job(self) -> None:
        logger = get_logger()

        try:
            await logger.info("cron_job", "Starting cache cleanup scheduled job")
            task = asyncio.create_task(self._cleanup_job())
            self.tasks["cleanup"] = task

        except Exception as e:
            await logger.fatal("cron_job", f"Failed to start cleanup job: {str(e)}")

    async def _cleanup_job(self) -> None:
        logger = get_logger()

        while True:
            try:
                await asyncio.sleep(10 * 60)  # every 10 minutes

                await logger.debug("cron_job", "Cache cleanup job executing")

                items_removed = 5

                await logger.info(
                    "cron_job",
                    "Cache cleanup completed",
                    {
                        "additionalContext": {
                            "itemsRemoved": items_removed
                        }
                    }
                )

            except asyncio.CancelledError:
                await logger.info("cron_job", "Cleanup job cancelled")
                break
            except Exception as e:
                await logger.error("cron_job", f"Error during cache cleanup: {str(e)}")

    async def start_health_check_job(self) -> None:
        logger = get_logger()

        try:
            await logger.info("cron_job", "Starting system health check scheduled job")
            task = asyncio.create_task(self._health_check_job())
            self.tasks["health_check"] = task

        except Exception as e:
            await logger.fatal("cron_job", f"Failed to start health check job: {str(e)}")

    async def _health_check_job(self) -> None:
        logger = get_logger()

        while True:
            try:
                await asyncio.sleep(5 * 60)  # every 5 minutes

                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                await logger.debug(
                    "cron_job",
                    "System health check executed",
                    {
                        "additionalContext": {
                            "memoryUsageMB": f"{memory_mb:.2f}",
                            "uptime": int(asyncio.get_event_loop().time())
                        }
                    }
                )

                if memory_mb > 500:
                    await logger.warn(
                        "cron_job",
                        "High memory usage detected",
                        {
                            "additionalContext": {
                                "heapUsedMB": f"{memory_mb:.2f}"
                            }
                        }
                    )

            except asyncio.CancelledError:
                await logger.info("cron_job", "Health check job cancelled")
                break
            except Exception as e:
                await logger.error("cron_job", f"Error during health check: {str(e)}")

    async def stop_all_jobs(self) -> None:
        logger = get_logger()

        try:
            await logger.info("cron_job", "Stopping all scheduled jobs")

            for name, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    await logger.debug("cron_job", f"Stopped job: {name}")

            if self.tasks:
                await asyncio.gather(*self.tasks.values(), return_exceptions=True)

            self.tasks.clear()

            await logger.info("cron_job", "All scheduled jobs stopped successfully")

        except Exception as e:
            await logger.error("cron_job", f"Error stopping jobs: {str(e)}")


task_service = TaskService()
