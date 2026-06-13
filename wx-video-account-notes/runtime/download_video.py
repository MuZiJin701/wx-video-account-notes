from __future__ import annotations

from pathlib import Path


def download_video(video_url: str, destination: Path) -> None:
    import httpx

    from runtime._retry import retry_call

    def _download() -> None:
        with httpx.stream("GET", video_url, follow_redirects=True, timeout=120.0) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0)) or None
            try:
                from tqdm import tqdm

                progress = tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"Downloading {destination.name}",
                )
            except ImportError:
                progress = None

            with destination.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
                    if progress is not None:
                        progress.update(len(chunk))

            if progress is not None:
                progress.close()

    retry_call(_download, description=f"download video to {destination.name}")
