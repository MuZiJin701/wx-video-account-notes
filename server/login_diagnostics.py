"""Allowlisted login diagnostics; never emit page text, URLs, or browser errors."""

import json
import re
from urllib.parse import urlsplit


def site(url):
    host = urlsplit(url).hostname or ""
    if host == "localhost.ptlogin2.qq.com":
        return "QQ_LOCAL_CLIENT"
    if host in {"yuanbao.tencent.com", "graph.qq.com", "mail.qq.com", "wx.mail.qq.com"}:
        return {"yuanbao.tencent.com": "YUANBAO", "graph.qq.com": "QQ_AUTH",
                "mail.qq.com": "MAIL", "wx.mail.qq.com": "MAIL"}[host]
    if host.endswith(".ptlogin2.qq.com"):
        return "QQ_LOGIN"
    if any(host == suffix or host.endswith("." + suffix)
           for suffix in ("captcha.qq.com", "captcha.qcloud.com", "captcha.gtimg.com", "captcha.gtimg.cn")):
        return "CAPTCHA"
    return "OTHER"


def report_login(stage, page):
    print("LOGIN_STAGE " + stage, flush=True)
    if stage == "BROWSER_READY":
        def failed(request):
            category = site(request.url)
            if category not in {"OTHER", "QQ_LOCAL_CLIENT"} and request.failure != "net::ERR_ABORTED":
                failure = request.failure or ""
                reason = failure if re.fullmatch(r"net::ERR_[A-Z0-9_]{1,64}", failure) else "OTHER"
                print(f"LOGIN_NETWORK_FAILED {category} {reason}", flush=True)

        def response_received(response):
            category = site(response.url)
            if category != "OTHER" and response.status >= 400:
                print(f"LOGIN_HTTP {category} {response.status}", flush=True)
            if category == "QQ_LOGIN" and urlsplit(response.url).path.rsplit("/", 1)[-1] in {"check", "login", "pt4_auth"}:
                print(f"LOGIN_QQ_RESPONSE {response.status}", flush=True)
                try:
                    match = re.search(r"(ptuiCB|ptui_checkVC)\(\s*['\"]([0-9]{1,5})['\"]", response.text()[:512])
                    if match:
                        kind = "LOGIN" if match[1] == "ptuiCB" else "CHECK"
                        print(f"LOGIN_QQ_RESULT {kind} {match[2]}", flush=True)
                    else:
                        print("LOGIN_QQ_RESULT UNRECOGNIZED", flush=True)
                except Exception:
                    print("LOGIN_QQ_RESULT UNAVAILABLE", flush=True)

        page.on("requestfailed", failed)
        page.on("response", response_received)
        page.on("pageerror", lambda _: print("LOGIN_JAVASCRIPT_ERROR", flush=True))
    if stage != "FAILED":
        return
    state = {"site": site(page.url), "frames": [], "signals": []}
    patterns = {
        "PASSWORD_ERROR": r"密码错误|密码不正确|帐号或密码错误|账号或密码错误",
        "ACCOUNT_RESTRICTED": r"操作.*频繁|帐号.*冻结|账号.*冻结|登录环境.*异常",
        "VERIFICATION": r"安全验证|身份验证|短信验证|拖动.*滑块|完成.*拼图|扫码验证|验证码",
        "SKIP_BINDING": r"^跳过[，,、\s]*直接登录$",
        "AUTHORIZE": r"^(授权并登录|授权登录|同意并登录|同意授权|确认授权|同意)$",
    }
    for frame in page.frames:
        state["frames"].append(site(frame.url))
        try:
            if frame.name == "ptlogin_iframe":
                keys = ("hasDomLoad", "hasVCSuccess", "checkState", "checkRet", "needVc", "needShowNewVc",
                        "vcFlag", "smsCheck", "needSms", "isCheckTimeout", "cntCheckTimeout")
                flags = frame.evaluate("keys => Object.fromEntries(keys.map(k => [k, window.pt?.plogin?.[k]]))", keys)
                state["qq_flags"] = {key: flags[key] for key in keys if key in flags
                                     and (type(flags[key]) is bool or type(flags[key]) is int and -1 <= flags[key] <= 999)}
            error = frame.locator("#err_m, #error_tips")
            if any(item.is_visible() for item in error.all()):
                state["signals"].append("LOGIN_ERROR_VISIBLE")
            for name, pattern in patterns.items():
                if any(item.is_visible() for item in frame.get_by_text(re.compile(pattern)).all()):
                    state["signals"].append(name)
            if any(item.is_visible() for item in frame.get_by_role("button", name=re.compile(patterns["AUTHORIZE"])).all()):
                state["signals"].append("AUTHORIZE_CONTROL")
        except Exception:
            state["signals"].append("FRAME_UNAVAILABLE")
    state["frames"] = sorted(set(state["frames"]))
    state["signals"] = sorted(set(state["signals"]))
    print("LOGIN_STATE " + json.dumps(state, sort_keys=True), flush=True)
