from __future__ import annotations

import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.asr_runner import resolve_asr_model_dir, resolve_asr_runtime, run_asr


class AsrRunnerTests(unittest.TestCase):
    def test_resolve_asr_runtime_scales_from_cpu_count_instead_of_fixed_numbers(self) -> None:
        self.assertEqual(resolve_asr_runtime(cpu_count=2), (2, 1))
        self.assertEqual(resolve_asr_runtime(cpu_count=4), (2, 2))
        self.assertEqual(resolve_asr_runtime(cpu_count=8), (4, 2))
        self.assertEqual(resolve_asr_runtime(cpu_count=32), (16, 2))

    def test_resolve_asr_model_dir_returns_whisper_model_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_root = Path(temp_dir)
            whisper_dir = runtime_root / "models" / "whisper" / "tiny"
            whisper_dir.mkdir(parents=True)
            (whisper_dir / "config.json").write_text("{}", encoding="utf-8")

            path = resolve_asr_model_dir(runtime_root, "faster-whisper")
            self.assertEqual(path, whisper_dir)

    def test_run_asr_rejects_unknown_provider(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported ASR provider"):
            run_asr(Path("demo.wav"), Path("model"), provider="unknown")

    def test_run_asr_uses_faster_whisper(self) -> None:
        class FakeSegment:
            def __init__(self, text):
                self.text = text

        class FakeModel:
            def __init__(self, model_path, device, compute_type, cpu_threads, num_workers):
                self.cpu_threads = cpu_threads
                self.num_workers = num_workers
                self.device = device
                self.compute_type = compute_type

            def transcribe(self, audio_path, language):
                return ([FakeSegment("第一段"), FakeSegment("第二段")], None)

        with patch.dict(sys.modules, {
            "faster_whisper": types.SimpleNamespace(WhisperModel=FakeModel),
        }), patch("runtime.asr_runner.os.cpu_count", return_value=8):
            text = run_asr(Path("demo.wav"), Path("model"))

        self.assertEqual(text, "第一段\n第二段")


if __name__ == "__main__":
    unittest.main()
