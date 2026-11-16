"""Publish Penumbra to Hugging Face Spaces (run on the machine that has the data; log in first with `hf auth login`).

    python deploy/huggingface/publish.py              stage the runtime data, upload it, create/update the Space
    python deploy/huggingface/publish.py --space-only update only the Space files (Dockerfile, README, fetch script)

What it uploads:
  <user>/penumbra-data (private dataset): the files the running app reads, measured by tracing a full run of the
    app (5 m site surfaces, LOLA maps, SPICE kernels, star catalogue, precomputed cache, metadata), the north LOLA
    maps used to build polar imagery on demand, and tiles.tar (the built globe imagery). About 1.4 GB.
  <user>/penumbra (public Docker Space): Dockerfile, README and fetch_data.py from this folder. The Space builds the
    code from GitHub and reads the dataset with the DATA_TOKEN secret, which this script sets to your token.
"""
from __future__ import annotations

import argparse
import os
import shutil
import tarfile
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi, get_token

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WS = ROOT.parent
STAGE = WS / "hf_staging"  # outside the repository; same drive, so files are hard-linked, not copied
TILE_PARTS = ["manifest.json", "ldem16.bin", "polar_n_coarse.bin", "polar_s_coarse.bin", "tp_s", "tp_n", "wac", "site"]


def raw(rel: str, legacy: str) -> Path:
    p = ROOT / "data" / "raw" / rel
    return p if p.exists() else WS / legacy


def runtime_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for sub in ("spice", "lola", "stars"):
        files += [(p, f"data/raw/{sub}/{p.name}") for p in sorted((ROOT / "data/raw" / sub).iterdir()) if p.is_file()]
    for p in sorted((ROOT / "data/raw/pgda78").glob("Site*/Site*_final_adj_5mpp_surf.tif")):
        files.append((p, f"data/raw/pgda78/{p.parent.name}/{p.name}"))
    for name in ("ldem_80n_80m.img", "ldem_80n_80m.lbl", "ldem_75n_240m.img", "ldem_75n_240m.lbl"):
        p = raw(f"lola_north/{name}", f"penumbra_prep/data/raw/lola_north/{name}")
        if p.exists():
            files.append((p, f"data/raw/lola_north/{name}"))
    for p in sorted((ROOT / "data/cache").rglob("*")):
        if p.is_file():
            files.append((p, p.relative_to(ROOT).as_posix()))
    files += [(p, f"data/metadata/{p.name}") for p in sorted((ROOT / "data/metadata").glob("*.json"))]
    return files


def stage() -> None:
    if (STAGE / "data").exists():
        shutil.rmtree(STAGE / "data")
    STAGE.mkdir(exist_ok=True)
    total = 0
    for src, rel in runtime_files():
        dst = STAGE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
        total += src.stat().st_size
    print(f"data: {total / 1e6:.0f} MB staged", flush=True)
    tar = STAGE / "tiles.tar"
    with tarfile.open(tar, "w") as t:
        for part in TILE_PARTS:
            t.add(ROOT / "tiles" / part, arcname=f"tiles/{part}",
                  filter=lambda ti: None if ti.name.endswith(".log") else ti)
    print(f"tiles.tar: {tar.stat().st_size / 1e6:.0f} MB", flush=True)
    (STAGE / "README.md").write_text(
        "# Penumbra runtime data (private)\n\nFiles the Penumbra app reads at run time, from NASA/JPL and partner "
        "archives (see docs/DATA_PROVENANCE.md in github.com/SammamMahdi/Penumbra), plus its precomputed cache and "
        "built globe imagery. Written by deploy/huggingface/publish.py.\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space-only", action="store_true", help="only update the Space files")
    ap.add_argument("--space", default="penumbra")
    ap.add_argument("--dataset", default="penumbra-data")
    a = ap.parse_args()
    api, token = HfApi(), get_token()
    if not token:
        raise SystemExit("Not logged in: run `hf auth login` first.")
    user = api.whoami()["name"]
    data_repo, space_repo = f"{user}/{a.dataset}", f"{user}/{a.space}"

    if not a.space_only:
        stage()
        api.create_repo(data_repo, repo_type="dataset", private=True, exist_ok=True)
        api.upload_large_folder(repo_id=data_repo, folder_path=STAGE, repo_type="dataset", num_workers=2,
                                allow_patterns=["data/**", "tiles.tar", "README.md"])
        print(f"dataset uploaded: https://huggingface.co/datasets/{data_repo}", flush=True)

    api.create_repo(space_repo, repo_type="space", space_sdk="docker", exist_ok=True)
    api.add_space_secret(space_repo, "DATA_TOKEN", token)
    docker = (HERE / "Dockerfile").read_text(encoding="utf-8").replace("__DATA_REPO__", data_repo)
    ops = [CommitOperationAdd("Dockerfile", docker.encode()),
           CommitOperationAdd("README.md", str(HERE / "README.md")),
           CommitOperationAdd("fetch_data.py", str(HERE / "fetch_data.py"))]
    api.create_commit(space_repo, ops, repo_type="space", commit_message="Deploy Penumbra")
    print(f"space: https://huggingface.co/spaces/{space_repo}  (app: https://{user.lower()}-{a.space}.hf.space)", flush=True)


if __name__ == "__main__":
    main()
