"""Real Chromium smoke check; uses no account, secrets, or external website."""

from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright


def main() -> None:
    with TemporaryDirectory() as directory, sync_playwright() as playwright:
        profile = Path(directory) / "profile"
        for run in range(2):
            context = playwright.chromium.launch_persistent_context(
                str(profile), channel="chromium", headless=True, locale="zh-CN",
            )
            try:
                page = context.pages[0]
                page.set_content("<title>wx-notes browser smoke</title><button>检查</button>")
                assert page.title() == "wx-notes browser smoke"
                assert page.get_by_role("button", name="检查").is_visible()
                assert page.evaluate("1 + 1") == 2
                if run == 0:
                    context.add_cookies([{"name": "smoke", "value": "placeholder", "url": "https://example.invalid/", "expires": 4_102_444_800}])
                else:
                    assert any(c["name"] == "smoke" and c["value"] == "placeholder" for c in context.cookies("https://example.invalid/"))
            finally:
                context.close()
    print("BROWSER_SMOKE_OK")


if __name__ == "__main__":
    main()
