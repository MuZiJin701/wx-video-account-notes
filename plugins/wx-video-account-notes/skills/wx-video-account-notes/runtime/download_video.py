from __future__ import annotations

from pathlib import Path


def download_file(url: str, destination: Path, *, description: str) -> None:
    import httpx

    from runtime._retry import retry_call

    def _download() -> None:
        with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
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

    retry_call(_download, description=description)


def download_video(video_url: str, destination: Path) -> None:
    download_file(video_url, destination, description=f"download video to {destination.name}")


def download_images(image_urls: list[str], frames_dir: Path) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for frame_path in frames_dir.glob("*.jpg"):
        frame_path.unlink()

    downloaded: list[Path] = []
    for index, image_url in enumerate(image_urls, start=1):
        destination = frames_dir / f"{index:03d}.jpg"
        download_file(image_url, destination, description=f"download image to {destination.name}")
        downloaded.append(destination)
    return downloaded
