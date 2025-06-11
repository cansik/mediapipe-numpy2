#!/usr/bin/env python3
"""
download_wheels.py: Multithreaded downloader for mediapipe .whl files with rich progress bars
and SHA256 checksum verification against PyPI metadata.

Usage:
    ./download_wheels.py [version] [download_dir]

If version is 'latest' or omitted, fetches the latest release.
Requires: requests, rich
"""

import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn,
)


def get_latest_version() -> str:
    resp = requests.get('https://pypi.org/pypi/mediapipe/json')
    resp.raise_for_status()
    return resp.json()['info']['version']


def fetch_file_list(version: str) -> list[dict]:
    url = f'https://pypi.org/pypi/mediapipe/{version}/json'
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return [
        f for f in data.get('urls', [])
        if f.get('packagetype') == 'bdist_wheel'
    ]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fd:
        for chunk in iter(lambda: fd.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def download_file(
        file_info: dict,
        download_dir: Path,
        progress: Progress,
        task_id: int
):
    fname = file_info['filename']
    expected_sha = file_info.get('digests', {}).get('sha256')
    url = file_info['url']
    dest = download_dir / fname

    # 1) if file exists, check its SHA256
    if dest.exists() and expected_sha:
        if sha256_of(dest).lower() == expected_sha.lower():
            progress.update(task_id, advance=1)
            return
        else:
            dest.unlink()  # bad checksum, force re-download

    # 2) otherwise stream-download with a per-file progress bar
    r = requests.get(url, stream=True)
    r.raise_for_status()
    total = int(r.headers.get('Content-Length', 0))
    subtask = progress.add_task(fname, total=total)

    with dest.open('wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress.update(subtask, advance=len(chunk))

    progress.update(subtask, completed=total)
    progress.update(task_id, advance=1)


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else 'latest'
    download_dir = Path(sys.argv[2] if len(sys.argv) > 2 else './downloaded_wheels')

    if version.lower() == 'latest':
        print("Fetching latest mediapipe version…")
        version = get_latest_version()
        print(f"Latest version is {version}")

    wheels = fetch_file_list(version)
    if not wheels:
        print(f"No wheel files found for mediapipe=={version}", file=sys.stderr)
        sys.exit(1)

    download_dir.mkdir(parents=True, exist_ok=True)
    total = len(wheels)

    # one combined progress bar for both total and per-file
    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TextColumn("• {task.completed}/{task.total} files")
    )

    with progress:
        overall = progress.add_task("[bold]Downloading wheels", total=total)
        with ThreadPoolExecutor(max_workers=min(8, total)) as pool:
            futures = [
                pool.submit(download_file, info, download_dir, progress, overall)
                for info in wheels
            ]
            for future in as_completed(futures):
                if exc := future.exception():
                    print(f"Error: {exc}", file=sys.stderr)

    print("All downloads complete.")


if __name__ == "__main__":
    main()
