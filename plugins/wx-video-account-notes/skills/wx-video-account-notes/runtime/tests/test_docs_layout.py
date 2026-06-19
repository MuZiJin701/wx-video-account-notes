from __future__ import annotations

import unittest
from pathlib import Path


class DocsLayoutTests(unittest.TestCase):
    def test_project_level_docs_exist_for_human_facing_skill_docs(self) -> None:
        current = Path(__file__).resolve()
        docs_root = next(
            parent
            for parent in current.parents
            if (parent / "README.md").exists() and (parent / ".agents").exists()
        )

        self.assertTrue((docs_root / "README.md").exists())
        self.assertTrue((docs_root / "CHANGELOG.md").exists())
        self.assertTrue((docs_root / "目录说明.md").exists())


if __name__ == "__main__":
    unittest.main()
