"""Image build step: download Penumbra's runtime data from the private Hugging Face dataset into the app folder.

    python fetch_data.py <owner>/penumbra-data

Downloads data/ (raw files the app reads, the precomputed cache and metadata) and tiles.tar (the built globe
imagery), then unpacks the tiles. The token comes from the DATA_TOKEN build secret.
"""
import os
import sys
import tarfile
from pathlib import Path

from huggingface_hub import snapshot_download

APP = Path("/home/user/app")
SECRET = Path("/run/secrets/DATA_TOKEN")
token = SECRET.read_text().strip() if SECRET.exists() else os.environ.get("DATA_TOKEN")

snapshot_download(repo_id=sys.argv[1], repo_type="dataset", local_dir=APP, token=token,
                  allow_patterns=["data/**", "tiles.tar"], max_workers=4)
tar = APP / "tiles.tar"
with tarfile.open(tar) as t:
    t.extractall(APP, filter="data")
tar.unlink()
print("data:", sum(f.stat().st_size for f in (APP / "data").rglob("*") if f.is_file()) // 10**6, "MB;",
      "tiles:", sum(1 for f in (APP / "tiles").rglob("*") if f.is_file()), "files", flush=True)
