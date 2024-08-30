from bot import Bot
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    app = Bot()

    try:
        await app.start()
        logger.info(f"Bot @{app.username} is running...")
        # Keep the bot running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt. Stopping bot...")
    finally:
        await app.stop()
        logger.info("Bot has been stopped.")

if __name__ == "__main__":
    asyncio.run(main())
