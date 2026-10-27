from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG = json.loads(Path(__file__).with_name("resolver_config.json").read_text(encoding="utf-8"))


def _video_urls(payload: dict) -> list[str]:
    feed_info = payload.get("data", {}).get("feedInfo", {})
    urls = []
    for key in ("h264VideoInfo", "h265VideoInfo"):
        info = feed_info.get(key)
        url = info.get("videoUrl") if isinstance(info, dict) else None
        if isinstance(url, str) and url and url not in urls:
            urls.append(url)
    url = feed_info.get("videoUrl")
    if isinstance(url, str) and url and url not in urls:
        urls.append(url)
    return urls


def _pick_image_urls(payload: dict) -> list[str]:
    feed_info = payload.get("data", {}).get("feedInfo", {})
    urls: list[str] = []
    for item in feed_info.get("picInfo") or []:
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])
    return urls


def parse_worker_payload(payload: dict) -> dict:
    author_info = payload.get("data", {}).get("authorInfo", {})
    feed_info = payload.get("data", {}).get("feedInfo", {})
    image_urls = _pick_image_urls(payload)
    bgm = feed_info.get("bgmInfo")
    bgm = bgm if isinstance(bgm, dict) else {}
    video_urls = _video_urls(payload)
    if not video_urls and not image_urls and not feed_info.get("coverUrl"):
        raise RuntimeError("No downloadable media URL found in resolver response")
    video_url = video_urls[0] if video_urls else ""
    media_type = "video" if video_urls else "image"
    return {
        "video_url": video_url,
        "video_urls": video_urls,
        "image_urls": image_urls,
        "cover_url": feed_info.get("coverUrl") or "",
        "bgm_urls": [url for url in dict.fromkeys(bgm.get(key) for key in ("bgmUrl", "mediaStreamingUrl")) if url],
        "feed_info": feed_info,
        "media_type": media_type,
        "author": author_info.get("nickname") or feed_info.get("nickname") or feed_info.get("authorName") or "",
        "title": feed_info.get("description") or feed_info.get("desc") or feed_info.get("title") or "",
        "raw_text": json.dumps(payload, ensure_ascii=False, indent=2),
    }


def resolve_share_link(share_url: str) -> dict:
    import httpx
    configured_url = os.environ.get("WX_VIDEO_ACCOUNT_RESOLVE_API", "").strip()
    configured_key = os.environ.get("WX_VIDEO_ACCOUNT_RESOLVE_KEY", "").strip()
    if bool(configured_url) != bool(configured_key):
        raise RuntimeError("自部署解析服务需要同时设置 WX_VIDEO_ACCOUNT_RESOLVE_API 和 WX_VIDEO_ACCOUNT_RESOLVE_KEY。")
    api_url = configured_url or _CONFIG["api_url"]
    access_key = configured_key or _CONFIG["access_key"]
    try:
        response = httpx.get(
            api_url,
            params={"url": share_url},
            headers={"Authorization": f"Bearer {access_key}"},
            timeout=70.0,
        )
    except httpx.RequestError as exc:
        raise RuntimeError("解析服务不可达，请检查所选服务或稍后重试。") from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("解析服务返回了无效响应，请联系所选服务的维护者。") from exc
    code = payload.get("code") if isinstance(payload, dict) else None
    if response.status_code != 200 or code != "OK":
        messages = {
            "UNAUTHORIZED": "解析凭证不匹配，请检查所选服务的访问凭证。",
            "RATE_LIMITED": "解析请求过于频繁，请稍后重试。",
            "INVALID_LINK": "视频号分享链接格式不正确。",
            "LOGIN_REQUIRED": "解析服务缺少元宝登录态，请联系所选服务的维护者更新 Cookie。",
            "LOGIN_EXPIRED_OR_UPSTREAM_CHANGED": "元宝登录态可能失效或上游接口已变化，请联系所选服务的维护者检查。",
            "FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED": "媒体动态不可用或上游接口已变化，请换可用链接或联系所选服务的维护者。",
            "RESOLVER_UNAVAILABLE": "解析服务暂时不可用，请稍后重试或联系所选服务的维护者。",
        }
        raise RuntimeError(messages.get(code, "解析失败，请联系所选服务的维护者检查状态。"))
    feed = payload.get("data")
    if not isinstance(feed, dict):
        raise RuntimeError("解析服务返回了无效媒体数据，请联系所选服务的维护者。")
    try:
        resolved = parse_worker_payload(feed)
    except (AttributeError, RuntimeError, TypeError) as exc:
        raise RuntimeError("媒体动态缺少可下载内容，请换可用链接或联系所选服务的维护者。") from exc
    resolved["raw_text"] = json.dumps(payload, ensure_ascii=False, indent=2)
    return resolved
