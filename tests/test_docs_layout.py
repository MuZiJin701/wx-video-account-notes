from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsLayoutTests(unittest.TestCase):
    def test_project_level_docs_exist_for_human_facing_skill_docs(self) -> None:
        for name in ("README.md", "CHANGELOG.md", "目录说明.md", "docs/test-cases.md"):
            self.assertTrue((REPO_ROOT / name).is_file(), name)

    def test_codex_package_contains_only_the_client_distribution(self) -> None:
        index = REPO_ROOT / ".agents/plugins/marketplace.json"
        (entry,) = json.loads(index.read_text(encoding="utf-8"))["plugins"]
        plugin = REPO_ROOT / entry["source"]["path"]
        self.assertEqual(plugin, REPO_ROOT / "plugin")
        manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        skill = plugin / manifest["skills"] / "wx-video-account-notes"
        self.assertTrue((skill / "SKILL.md").is_file())
        for relative in ("server", "docs", "tests"):
            self.assertFalse((plugin / relative).exists(), relative)
        self.assertFalse((skill / "runtime/tests").exists())
        self.assertFalse((skill / "tests").exists())


if __name__ == "__main__":
    unittest.main()
