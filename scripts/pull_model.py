import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings


def main():
    model = settings.ollama_model
    print(f"Pulling model: {model}")
    print(f"Size: ~2.5 GB (phi), ~4 GB (sqlcoder:7b)")
    result = subprocess.run(["ollama", "pull", model], capture_output=False)
    if result.returncode != 0:
        print(f"Failed to pull {model}")
        print("Install Ollama from https://ollama.com first")
        sys.exit(1)
    print(f"Model {model} ready!")


if __name__ == "__main__":
    main()