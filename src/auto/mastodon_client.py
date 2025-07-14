from mastodon import Mastodon
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from the project root .env file
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")
ACCESS_TOKEN = os.getenv("MASTODON_TOKEN")


def post_to_mastodon(status: str, visibility: str = "private"):
    """Post a status to Mastodon."""
    masto = Mastodon(access_token=ACCESS_TOKEN, api_base_url=MASTODON_INSTANCE)
    masto.toot(status, visibility=visibility)
    print("Posted to Mastodon!")


if __name__ == "__main__":
    post_to_mastodon("Hello world! My Substack → Socials bot is live 🚀")
