from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import zipfile
from pathlib import Path

from runtime.platform import detect_platform, runtime_root


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def asset_present(root: Path, pattern: str) -> bool:
    return any(root.glob(pattern))


def _verify_expected_files(root: Path, asset: dict) -> bool:
    expected_hash = asset.get("file_sha256")
    if not expected_hash:
        return True
    patterns = asset.get("expected_globs") or [asset["expected_glob"]]
    matches = [path for pattern in patterns for path in root.glob(pattern) if path.is_file()]
    return bool(matches) and all(_verify_sha256(path, expected_hash) for path in matches)


def asset_complete(root: Path, asset: dict, cache_root: Path | None = None) -> bool:
    patterns = asset.get("expected_globs") or [asset["expected_glob"]]
    if not all(asset_present(root, pattern) for pattern in patterns):
        return False
    if not _verify_expected_files(root, asset):
        return False
    archive_name = asset.get("archive_name")
    expected_archive_hash = asset.get("sha256")
    if cache_root and archive_name and expected_archive_hash:
        archive_path = cache_root / archive_name
        return archive_path.exists() and _verify_sha256(archive_path, expected_archive_hash)
    if cache_root and asset.get("archives"):
        for archive in asset["archives"]:
            archive_path = cache_root / archive["archive_name"]
            if archive_path.exists() and archive.get("sha256") and not _verify_sha256(archive_path, archive["sha256"]):
                return False
    return True


def _verify_sha256(path: Path, expected: str) -> bool:
    if not expected:
        return True
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    if actual != expected:
        print(f"[wx-video-account-notes][bootstrap] SHA256 mismatch: {path.name} expected={expected[:16]}... actual={actual[:16]}...")
        return False
    return True


def download_file(urls: list[str], destination: Path, sha256: str = "") -> None:
    import httpx

    from runtime._retry import retry_call

    def _download_single(url: str) -> None:
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
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

            tmp = destination.with_suffix(destination.suffix + ".tmp")
            try:
                with tmp.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        handle.write(chunk)
                        if progress is not None:
                            progress.update(len(chunk))
                if progress is not None:
                    progress.close()

                if sha256 and not _verify_sha256(tmp, sha256):
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(f"SHA256 verification failed for {destination.name}")

                tmp.replace(destination)
            except Exception:
                tmp.unlink(missing_ok=True)
                raise

    last_error: Exception | None = None
    for url_index, url in enumerate(urls):
        try:
            retry_call(lambda u=url: _download_single(u), description=f"download asset {destination.name}[{url_index}]")
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Failed to download asset to {destination}: {last_error}")


def extract_archive(archive_path: Path, target_root: Path) -> None:
    if archive_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_root)
        return

    if ".tar." in archive_path.name.lower():
        with tarfile.open(archive_path, "r:*") as archive:
            archive.extractall(target_root)
        return

    raise RuntimeError(f"Unsupported archive format: {archive_path.name}")


def ensure_asset(runtime_root: Path, cache_root: Path, asset: dict) -> None:
    target_root = ensure_dir(runtime_root / asset["target_subdir"])
    if asset_complete(target_root, asset, cache_root):
        return

    if "files" in asset:
        for file_spec in asset["files"]:
            destination = target_root / file_spec["path"]
            ensure_dir(destination.parent)
            if destination.exists() and _verify_sha256(destination, file_spec.get("sha256", "")):
                continue
            destination.unlink(missing_ok=True)
            download_file([file_spec["url"]], destination, sha256=file_spec.get("sha256", ""))
        if not asset_complete(target_root, asset, cache_root):
            raise RuntimeError(f"Asset {asset['name']} is still missing after file downloads")
        return

    if "repo_id" in asset:
        from huggingface_hub import snapshot_download

        local_dir = ensure_dir(target_root / asset["archive_name"])
        if local_dir.exists() and not _verify_expected_files(target_root, asset):
            shutil.rmtree(local_dir)
            local_dir.mkdir(parents=True)
        ensure_dir(local_dir / ".huggingface" / "download")
        snapshot_download(
            repo_id=asset["repo_id"],
            local_dir=local_dir,
        )
        if not asset_complete(target_root, asset, cache_root):
            shutil.rmtree(local_dir, ignore_errors=True)
            raise RuntimeError(f"Asset {asset['name']} is still missing after snapshot download")
        return

    archives = asset.get("archives") or [asset]
    for archive in archives:
        archive_path = cache_root / archive["archive_name"]
        if archive_path.exists() and archive.get("sha256") and not _verify_sha256(archive_path, archive["sha256"]):
            archive_path.unlink()
        if not archive_path.exists():
            download_file(archive["urls"], archive_path, sha256=archive.get("sha256", ""))
        if archive["extract"]:
            extract_archive(archive_path, target_root)
        else:
            shutil.copy2(archive_path, target_root / archive_path.name)

    if not asset_complete(target_root, asset, cache_root):
        raise RuntimeError(f"Asset {asset['name']} is still missing after extraction/copy")


def select_assets(assets: list[dict]) -> list[dict]:
    selected: list[dict] = []
    for asset in assets:
        policy = asset.get("install_policy", "required")
        if policy == "optional-gpu":
            continue
        selected.append(asset)
    return selected


def select_platform_asset(asset: dict, platform_id: str) -> dict:
    variants = asset.get("platforms")
    if not variants:
        return asset
    variant = variants.get(platform_id)
    if variant is None:
        raise RuntimeError(f"Asset {asset['name']} does not support {platform_id}")
    return {**asset, **variant}


def prune_runtime_cache(runtime_root: Path) -> None:
    cache_root = runtime_root / "cache"
    if cache_root.exists():
        shutil.rmtree(cache_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--runtime-root")
    parser.add_argument("--prune-cache", action="store_true")
    args = parser.parse_args()

    skill_root = Path(args.skill_root).resolve()
    platform_info = detect_platform()
    runtime_path = ensure_dir(Path(args.runtime_root).resolve()) if args.runtime_root else ensure_dir(runtime_root(skill_root, platform_info))
    if args.prune_cache:
        prune_runtime_cache(runtime_path)
    cache_root = ensure_dir(runtime_path / "cache")
    ensure_dir(runtime_path / "logs")
    ensure_dir(runtime_path / "tools")
    ensure_dir(runtime_path / "models")

    manifest = json.loads((skill_root / "runtime" / "assets_manifest.json").read_text(encoding="utf-8"))
    for asset in select_assets(manifest["assets"]):
        ensure_asset(runtime_path, cache_root, select_platform_asset(asset, platform_info.id))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
