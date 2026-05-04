import os
import subprocess
import shutil
from pathlib import Path

from scripts.config import Config


def _run(cmd: list[str], cwd: str) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def push_product(md_content: str, filename: str) -> str:
    repo_url = f"https://x-access-token:{Config.GITHUB_TOKEN}@github.com/{Config.REPO_PATH}.git"
    repo_dir = Path(Config.LOCAL_REPO_DIR)
    repo_posts = repo_dir / "src" / "content" / "posts"

    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    print(f"  [git] Cloning {Config.REPO_PATH}...")
    _run(["git", "clone", repo_url, str(repo_dir)], cwd=".")

    file_path = repo_posts / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(md_content, encoding="utf-8")

    _run(["git", "add", f"src/content/posts/{filename}"], cwd=str(repo_dir))
    _run(["git", "commit", "-m", f"Add product: {filename.replace('.md', '')}"], cwd=str(repo_dir))
    _run(["git", "push"], cwd=str(repo_dir))

    shutil.rmtree(repo_dir)

    raw_name = filename.replace(".md", "").replace("\\", "/")
    url = f"{Config.SITE_URL}/posts/{raw_name}/"
    print(f"  [git] Pushed & deployed: {url}")
    return url
