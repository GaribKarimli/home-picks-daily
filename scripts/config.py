import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AMAZON_TAG: str = os.getenv("AMAZON_TAG", "dummy-20")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REPO_PATH: str = os.getenv("REPO_PATH", "GaribKarimli/home-picks-daily")
    SITE_URL: str = "https://home-picks-daily.vercel.app"
    LOCAL_REPO_DIR: str = "repo_cache"

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if missing:
            raise ValueError(
                f"Missing required env vars: {', '.join(missing)}. "
                f"Check your .env file."
            )
