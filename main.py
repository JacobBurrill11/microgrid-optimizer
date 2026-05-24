import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")

from core.simulation import run_simulation

if __name__ == "__main__":
    run_simulation(use_real_weather=True)
