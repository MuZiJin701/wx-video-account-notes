from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsLayoutTests(unittest.TestCase):
    def test_project_level_docs_exist_for_human_facing_skill_docs(self) -> None:
        for name in ("README.md", "CHANGELOG.md", "目录说明.md", "docs/test-cases.md"):
            self.assertTrue((REPO_ROOT / name).is_file(), name)

    def test_native_marketplaces_share_the_client_package(self) -> None:
        for index, source in (
            (".agents/plugins/marketplace.json", {"source": "local", "path": "./plugin"}),
            (".claude-plugin/marketplace.json", "./plugin"),
            (".github/plugin/marketplace.json", "./plugin"),
            (".grok-plugin/marketplace.json", {"type": "local", "path": "./plugin"}),
            (".cursor-plugin/marketplace.json", "plugin"),
        ):
            with self.subTest(index=index):
                catalog = json.loads((REPO_ROOT / index).read_text(encoding="utf-8"))
                (entry,) = catalog["plugins"]
                self.assertEqual(catalog["name"], "wx-video-account-notes-dev")
                self.assertEqual(entry["name"], "wx-video-account-notes")
                self.assertEqual(entry["source"], source)

    def test_plugin_package_contains_only_the_client_distribution(self) -> None:
        plugin = REPO_ROOT / "plugin"
        manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(manifest["name"], "wx-video-account-notes")
        self.assertEqual(manifest["extensions"]["com.openai"]["interface"]["displayName"], manifest["name"])
        for vendor in (".claude-plugin", ".cursor-plugin", ".grok-plugin"):
            native = json.loads((plugin / vendor / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(native["name"], manifest["name"])
        (skill,) = (plugin / "skills").iterdir()
        self.assertEqual(skill.name, manifest["name"])
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertIn("disable-model-invocation: true", (skill / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn(
            "allow_implicit_invocation: false",
            (skill / "agents/openai.yaml").read_text(encoding="utf-8"),
        )
        for relative in ("server", "docs", "tests"):
            self.assertFalse((plugin / relative).exists(), relative)
        self.assertFalse((skill / "runtime/tests").exists())
        self.assertFalse((skill / "tests").exists())


if __name__ == "__main__":
    unittest.main()
