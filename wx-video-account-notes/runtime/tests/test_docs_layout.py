from __future__ import annotations

import unittest
from pathlib import Path


class DocsLayoutTests(unittest.TestCase):
    def test_project_level_docs_exist_for_human_facing_skill_docs(self) -> None:
        project_root = Path(__file__).resolve().parents[3]
        docs_root = project_root

        self.assertTrue((docs_root / "README.md").exists())
        self.assertTrue((docs_root / "CHANGELOG.md").exists())
        self.assertTrue((docs_root / "目录说明.md").exists())


if __name__ == "__main__":
    unittest.main()
