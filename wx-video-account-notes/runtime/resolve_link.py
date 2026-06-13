from __future__ import annotations

import json
import os

_DEFAULT_API_URL = "https://sph.litao.workers.dev/api/fetch_video_profile"


def _resolve_api_url() -> str:
    return os.environ.get("WX_VIDEO_ACCOUNT_RESOLVE_API", "").strip() or _DEFAULT_API_URL


def _pick_video_url(payload: dict) -> str:
    feed_info = payload.get("data", {}).get("feedInfo", {})
    for path in (("h264VideoInfo", "videoUrl"), ("h265VideoInfo", "videoUrl"), ("videoUrl",)):
        cursor = feed_info
        for key in path:
            if not isinstance(cursor, dict) or key not in cursor:
                cursor = None
                break
            cursor = cursor[key]
        if cursor:
            return cursor
    raise RuntimeError("No downloadable video URL found in worker response")


def parse_worker_payload(payload: dict) -> dict:
    video_url = _pick_video_url(payload)
    author_info = payload.get("data", {}).get("authorInfo", {})
    feed_info = payload.get("data", {}).get("feedInfo", {})
    return {
        "video_url": video_url,
        "author": author_info.get("nickname") or feed_info.get("nickname") or feed_info.get("authorName") or "",
        "title": feed_info.get("description") or feed_info.get("desc") or feed_info.get("title") or "",
        "raw_text": json.dumps(payload, ensure_ascii=False, indent=2),
    }


def resolve_share_link(share_url: str) -> dict:
    import httpx

    from runtime._retry import retry_call

    api_url = _resolve_api_url()

    def _call() -> dict:
        response = httpx.post(api_url, json={"url": share_url}, follow_redirects=True, timeout=60.0)
        response.raise_for_status()
        payload = response.json()
        return parse_worker_payload(payload)

    return retry_call(_call, description=f"resolve share link: {share_url[:60]}...")
