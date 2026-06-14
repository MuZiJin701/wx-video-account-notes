from __future__ import annotations

import unittest

from runtime.compose_note import build_note_materials, synthesize_markdown


class ComposeMarkdownNoteTests(unittest.TestCase):
    def test_build_note_materials_exports_cleaned_sections(self) -> None:
        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n振舟探影\n一旁的熊孩子居然将手",
            asr_text="她在成座电梯是金孔的发现\n电梯突然卡死在高层\n只能等待消防员赶来营救他们",
            ocr_error="",
            asr_error="",
        )

        self.assertEqual(materials["metadata"]["author"], "孤舟探影视")
        self.assertIn("一旁的熊孩子居然将手", materials["ocr_lines"])
        self.assertIn("电梯突然卡死在高层", materials["asr_lines"])
        self.assertIn("视频主线：", " ".join(materials["summary_lines"]))

    def test_build_note_materials_keeps_all_cleaned_lines_without_length_caps(self) -> None:
        ocr_text = "\n".join([f"## {index:03d}.jpg\n第{index}条字幕" for index in range(1, 9)])
        asr_text = "\n".join([f"第{index}条转写" for index in range(1, 31)])

        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "完整保留测试",
            },
            ocr_text=ocr_text,
            asr_text=asr_text,
            ocr_error="",
            asr_error="",
        )

        self.assertEqual(len(materials["ocr_lines"]), 8)
        self.assertEqual(len(materials["asr_lines"]), 30)
        self.assertIn("第8条字幕", materials["ocr_lines"])
        self.assertIn("第30条转写", materials["asr_lines"])

    def test_synthesize_markdown_produces_more_natural_note(self) -> None:
        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n一旁的熊孩子居然将手\n## 002.jpg\n长时间呆在狭小的空间里",
            asr_text="一旁的雄孩子居然江手\n放在了电梯的制动法案有上\n只能等待消防员赶来营救他们",
            ocr_error="",
            asr_error="",
        )

        markdown = synthesize_markdown(materials)

        self.assertIn("## 内容梗概", markdown)
        self.assertIn("## 提取到的文案", markdown)
        self.assertIn("## 转写文案", markdown)
        self.assertNotIn("## 画面文字", markdown)
        self.assertNotIn("## 口播转写（清洗后）", markdown)
        self.assertIn("熊孩子", markdown)
        self.assertIn("制动法案有上", markdown)
        self.assertIn("等待消防员赶来营救他们", markdown)
        self.assertIn("江手", markdown)

    def test_model_prompt_template_exists_for_final_note_stage(self) -> None:
        from pathlib import Path

        template_path = Path(__file__).resolve().parents[2] / "resources" / "model-note-template.md"
        self.assertTrue(template_path.exists())

    def test_builds_structured_note_with_source_labels_and_limits(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "GitHubStore",
                "title": "颠覆 3D 建模常识的新技术 R3",
            },
            ocr_text="## 001.jpg\n第一句\n第二句\n第三句\n第四句",
            asr_text="这是转写第一句。\n这是转写第二句。",
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("## 内容梗概", note)
        self.assertIn("来源：原始元数据", note)
        self.assertIn("## 提取到的文案", note)
        self.assertIn("## 转写文案", note)
        self.assertIn("## 提取状态", note)
        self.assertIn("GitHubStore", note)
        self.assertIn("这是转写第一句。", note)

    def test_marks_missing_asr_as_not_extracted(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "GitHubStore",
                "title": "没有口播的视频",
            },
            ocr_text="## 001.jpg\n画面上有两行说明文字",
            asr_text="",
            ocr_error="",
            asr_error="ASR produced no text",
        ))

        self.assertIn("这份转写文案基于提取内容重新顺写", note)
        self.assertIn("画面上有两行说明文字", note)
        self.assertIn("ASR：ASR produced no text", note)

    def test_cleans_repeated_asr_noise_and_generates_natural_summary(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n一旁的熊孩子居然将手\n## 002.jpg\n长时间呆在狭小的空间里",
            asr_text=(
                "一旁的熊孩子居然将手\n"
                "放在了电梯的制动按钮上\n"
                "电梯突然卡死在高层\n"
                "她是男生的男生的男生\n"
                "她是男生的男生的男生\n"
                "众人只能等待消防员救援"
            ),
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("## 内容梗概", note)
        self.assertIn("电梯突然卡死", note)
        self.assertIn("等待消防员救援", note)
        self.assertNotIn("她是男生的男生的男生", note)
        self.assertIn("悬疑惊悚", note)

    def test_preserves_non_repeated_lines_without_domain_specific_filters(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n振舟探影\n一旁的熊孩子居然将手\n狐身探影",
            asr_text="她在成座电梯是金孔的发现\n电梯突然卡死在高层\n只能等待消防员赶来营救他们",
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("振舟探影", note)
        self.assertIn("狐身探影", note)
        self.assertIn("她在成座电梯是金孔的发现", note)
        self.assertIn("电梯突然卡死在高层", note)

    def test_keeps_more_cleaned_asr_body_in_markdown(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n一旁的熊孩子居然将手",
            asr_text=(
                "一旁的雄孩子居然江手\n"
                "放在了电梯的制动法案有上\n"
                "这顺监就让她换了神\n"
                "身居也不受控制的左右搖盘\n"
                "就连呼吸都开始急速起来\n"
                "建此情形的雄孩子\n"
                "好奇的许问也也这人怎么了\n"
                "老头听后立即抵头向孫女解释\n"
                "说对方患有很严重的优秘恐惧者\n"
                "长时间待在下小的空间里\n"
                "只能等待消防员赶来营救他们"
            ),
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("## 转写文案", note)
        self.assertNotIn("## 口播转写（清洗后）", note)
        self.assertIn("说对方患有很严重的优秘恐惧者", note)
        self.assertIn("长时间待在下小的空间里", note)
        self.assertIn("只能等待消防员赶来营救他们", note)

    def test_markdown_preserves_full_cleaned_transcript_without_truncation(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "完整保留测试",
            },
            ocr_text="## 001.jpg\n第一条字幕\n## 002.jpg\n第二条字幕",
            asr_text="\n".join([f"第{index}条转写" for index in range(1, 16)]),
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("第15条转写", note)
        self.assertIn("第一条字幕", note)

    def test_extracted_copy_is_segmented_instead_of_single_overlong_line(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "作者",
                "title": "分段测试",
            },
            ocr_text="\n".join([f"## {index:03d}.jpg\nOCR第{index}句" for index in range(1, 7)]),
            asr_text="\n".join([f"ASR第{index}句" for index in range(1, 19)]),
            ocr_error="",
            asr_error="",
        ))

        self.assertNotIn("### 第 1 段", note)
        self.assertNotIn("### 第 2 段", note)
        self.assertIn("\n\nASR第1句；ASR第2句", note)
        self.assertIn("ASR第18句", note)

    def test_rewritten_copy_differs_from_raw_transcript_listing(self) -> None:
        note = synthesize_markdown(build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "作者",
                "title": "转写改写测试",
            },
            ocr_text="## 001.jpg\n字幕第一句\n## 002.jpg\n字幕第二句",
            asr_text="这是第一句内容\n这是第二句内容\n这是第三句内容",
            ocr_error="",
            asr_error="",
        ))

        self.assertIn("## 转写文案", note)
        self.assertIn("这份转写文案基于提取内容重新顺写", note)
        self.assertNotIn("- 这是第一句内容\n- 这是第二句内容\n- 这是第三句内容", note)

    def test_visual_frames_present_for_no_voice_video(self) -> None:
        from pathlib import Path

        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="no-voice",
            metadata={"author": "作者", "title": "无语音视频"},
            ocr_text="## 001.jpg\n画面文字",
            asr_text="",
            ocr_error="",
            asr_error="ASR produced no text",
            frame_paths=[Path(f"frame_{i:03d}.jpg") for i in range(1, 11)],
        )

        self.assertIn("visual_frames", materials)
        self.assertEqual(len(materials["visual_frames"]), 5)

    def test_visual_frames_absent_for_rich_voice_video(self) -> None:
        from pathlib import Path

        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="with-voice",
            metadata={"author": "作者", "title": "有丰富语音"},
            ocr_text="",
            asr_text="这是有充足语音的视频第一句内容测试字数是远超过五十字阈值的安全测试数据\n这是有充足语音的视频第二句内容测试字数也是远超下限的补充材料行",
            ocr_error="",
            asr_error="",
            frame_paths=[Path(f"frame_{i:03d}.jpg") for i in range(1, 11)],
        )

        self.assertNotIn("visual_frames", materials)

    def test_visual_frames_for_short_voice_below_50_chars(self) -> None:
        from pathlib import Path

        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="short-voice",
            metadata={"author": "作者", "title": "短语音"},
            ocr_text="",
            asr_text="只有几句",
            ocr_error="",
            asr_error="",
            frame_paths=[Path(f"frame_{i:03d}.jpg") for i in range(1, 11)],
        )

        self.assertIn("visual_frames", materials)
        self.assertGreaterEqual(len(materials["visual_frames"]), 1)

    def test_synthesize_markdown_uses_single_markdown_structure_without_draft_language(self) -> None:
        materials = build_note_materials(
            share_url="https://weixin.qq.com/sph/example",
            slug="demo-video",
            metadata={
                "author": "孤舟探影视",
                "title": "熊孩子随意按下电梯的急停按钮，结果导致所有人陷入一场危机当中#悬疑惊悚#影视解说",
            },
            ocr_text="## 001.jpg\n一旁的熊孩子居然将手",
            asr_text="电梯突然卡死在高层\n只能等待消防员赶来营救他们",
            ocr_error="",
            asr_error="",
        )

        markdown = synthesize_markdown(materials)

        self.assertIn("## 内容梗概", markdown)
        self.assertIn("## 提取到的文案", markdown)
        self.assertIn("## 转写文案", markdown)
        self.assertNotIn("草稿", markdown)


if __name__ == "__main__":
    unittest.main()
