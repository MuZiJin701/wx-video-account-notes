from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG = json.loads(Path(__file__).with_name("resolver_config.json").read_text(encoding="utf-8"))


def _resolve_api_url() -> str:
    return os.environ.get("WX_VIDEO_ACCOUNT_RESOLVE_API", "").strip() or _CONFIG["api_url"]


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
    raise RuntimeError("No downloadable video URL found in resolver response")


def _pick_image_urls(payload: dict) -> list[str]:
    feed_info = payload.get("data", {}).get("feedInfo", {})
    urls: list[str] = []
    for item in feed_info.get("picInfo") or []:
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])
    cover_url = feed_info.get("coverUrl")
    if cover_url and cover_url not in urls:
        urls.append(cover_url)
    return urls


def parse_worker_payload(payload: dict) -> dict:
    author_info = payload.get("data", {}).get("authorInfo", {})
    feed_info = payload.get("data", {}).get("feedInfo", {})
    image_urls = _pick_image_urls(payload)
    try:
        video_url = _pick_video_url(payload)
        media_type = "video"
    except RuntimeError:
        if not image_urls:
            raise
        video_url = ""
        media_type = "image"
    return {
        "video_url": video_url,
        "image_urls": image_urls,
        "media_type": media_type,
        "author": author_info.get("nickname") or feed_info.get("nickname") or feed_info.get("authorName") or "",
        "title": feed_info.get("description") or feed_info.get("desc") or feed_info.get("title") or "",
        "raw_text": json.dumps(payload, ensure_ascii=False, indent=2),
    }


def resolve_share_link(share_url: str) -> dict:
    import httpx
    api_url = _resolve_api_url()
    try:
        response = httpx.get(
            api_url,
            params={"url": share_url},
            headers={"Authorization": f"Bearer {_CONFIG['access_key']}"},
            timeout=70.0,
        )
    except httpx.RequestError as exc:
        raise RuntimeError("解析服务不可达，请稍后重试或联系维护者。") from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("解析服务返回了无效响应，请联系维护者。") from exc
    code = payload.get("code") if isinstance(payload, dict) else None
    if response.status_code != 200 or code != "OK":
        messages = {
            "UNAUTHORIZED": "解析凭证不匹配，请更新 Skill 或联系维护者。",
            "RATE_LIMITED": "解析请求过于频繁，请稍后重试。",
            "INVALID_LINK": "视频号分享链接格式不正确。",
            "LOGIN_REQUIRED": "解析服务缺少元宝登录态，请联系维护者更新 Cookie。",
            "LOGIN_EXPIRED_OR_UPSTREAM_CHANGED": "元宝登录态可能失效或上游接口已变化，请联系维护者检查。",
            "FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED": "媒体动态不可用或上游接口已变化，请换可用链接或联系维护者。",
            "RESOLVER_UNAVAILABLE": "解析服务暂时不可用，请稍后重试或联系维护者。",
        }
        raise RuntimeError(messages.get(code, "解析失败，请联系维护者检查服务状态。"))
    feed = payload.get("data")
    if not isinstance(feed, dict):
        raise RuntimeError("解析服务返回了无效媒体数据，请联系维护者。")
    try:
        resolved = parse_worker_payload(feed)
    except (AttributeError, RuntimeError, TypeError) as exc:
        raise RuntimeError("媒体动态缺少可下载内容，请换可用链接或联系维护者。") from exc
    resolved["raw_text"] = json.dumps(payload, ensure_ascii=False, indent=2)
    return resolved
