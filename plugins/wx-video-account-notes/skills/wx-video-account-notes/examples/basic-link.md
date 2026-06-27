输入示例：

```text
帮我处理这个视频号分享链接：https://weixin.qq.com/sph/AClgYpX4KB
```

期望结果：

- 自动初始化 `.runtime` 目录
- 下载视频或图文动态图片
- 生成 `note_materials.json`、`ocr.txt`、`asr.txt`、`frames/`，视频动态还会生成 `ocr_frames/` 和音频
- 生成同目录 Markdown 笔记
