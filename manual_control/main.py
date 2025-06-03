# manual_control/main.py
# To run:
# 1. cd to parent directory of 'manual_control'
# 2. manual_control/venv_manual_control/Scripts/activate  (or source .../bin/activate)
# 3. python -m manual_control.main

import asyncio
from .application import start_application # Import the new entry point

if __name__ == "__main__":
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        print("Application interrupted by user.")
    except Exception as e:
        print(f"Unhandled error in main: {e}")