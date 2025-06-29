# auto_soccer_bot/main.py
# To run:
# 1. cd to parent directory of 'auto_soccer_bot'
# 2. auto_soccer_bot\venv_auto_soccer\Scripts\activate
# 3. python -m auto_soccer_bot.main

import asyncio
from .application import start_auto_application # Import the new entry point

if __name__ == "__main__":
    try:
        asyncio.run(start_auto_application())
    except KeyboardInterrupt:
        print("Auto Soccer Bot Application interrupted by user.")
    except Exception as e:
        print(f"Unhandled error in auto_soccer_bot main: {e}")