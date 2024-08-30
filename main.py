import asyncio
from pyrogram import Client

# Ganti "my_bot" dengan nama atau ID sesi yang sesuai
app = Client("my_bot")

async def main():
    try:
        # Start the client
        await app.start()

        # Implement your main logic here
        print("Client started and running...")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        try:
            # Stop the client
            await app.stop()
            print("Client stopped successfully.")
        except ConnectionError:
            print("Client is already terminated or stopped.")

if __name__ == "__main__":
    asyncio.run(main())
