# 🎙️ 开源｜Qwen3-ASR：阿里最强开源语音识别，52种语言一键Docker部署

> 支持52种语言/方言、字级时间戳、流式转录，All-in-One Docker 一键部署，暗色主题炫酷UI

---

## 🎯 为什么做这个项目？

阿里最新发布的 Qwen3-ASR 是目前**业界最强的开源语音识别模型**，支持52种语言和方言。但官方只提供了 Gradio Demo 和 vLLM serve，距离生产可用还差很远：

**痛点一：部署太难**
- Transformers + CUDA + flash-attn 依赖地狱
- 三个模型（ASR + ForcedAligner）要分别下载配置
- 环境搭建动辄几个小时

**痛点二：没有好用的界面**
- 只有简陋的 Gradio Demo
- 没有麦克风录音、没有拖拽上传
- 移动端完全不可用

**痛点三：GPU管理粗暴**
- 模型加载后一直占着显存
- 不用也不释放，浪费宝贵的GPU资源
- 多模型切换要手动重启

**痛点四：缺少API和MCP**
- 没有标准的 REST API
- 无法被 AI Agent 调用
- 不能集成到自动化工作流

于是，**Qwen3-ASR Docker 一键部署**诞生了。

---

## 🚀 项目亮点

### 🌐 52种语言，22种中文方言

这是目前开源ASR中语言覆盖最广的：

**30种语言：** 中文、英语、日语、韩语、粤语、法语、德语、西班牙语、葡萄牙语、阿拉伯语、俄语、泰语、越南语、印尼语、意大利语、土耳其语、印地语、马来语、荷兰语、瑞典语、丹麦语、芬兰语、波兰语、捷克语、菲律宾语、波斯语、希腊语、罗马尼亚语、匈牙利语、马其顿语

**22种中文方言：** 四川话、粤语（广东/香港）、吴语、闽南语、东北话、河南话、湖南话、湖北话、江西话、山东话、陕西话、山西话、安徽话、福建话、甘肃话、贵州话、河北话、宁夏话、天津话、云南话、浙江话

支持**自动语言检测**，无需手动指定语言。

### ⏱️ 字级时间戳对齐

内置 Qwen3-ForcedAligner-0.6B，提供精确到每个字/词的时间戳：

```json
{
  "timestamps": [
    {"text": "你", "start": 0.0, "end": 0.28},
    {"text": "好", "start": 0.28, "end": 0.52},
    {"text": "世", "start": 0.52, "end": 0.78},
    {"text": "界", "start": 0.78, "end": 1.02}
  ]
}
```

点击UI中的时间戳，音频播放器自动跳转到对应位置。

### 🎨 暗色主题炫酷UI

纯 HTML/CSS/JS 打造，**绝不用 Gradio**：

- 🎵 **拖拽上传** + **麦克风录音**
- 🌐 **52种语言下拉选择**（分组：常用/中文方言/其他）
- 📊 **实时性能面板**：处理时间 / 音频时长 / RTF / GPU显存
- 🖥️ **GPU状态栏**：显存使用 + 模型状态 + 一键释放
- 🌍 **4语言切换**：简体中文 / 繁體中文 / English / 日本語
- 📱 **响应式设计**：手机也能用

### 🔄 流式转录

WebSocket 实时推送识别结果，边说边出文字，无需等待。

### 🧠 GPU 智能管理

- **懒加载**：首次请求时才加载模型
- **自动卸载**：空闲10分钟自动释放显存
- **手动释放**：UI上一键释放按钮
- **模型切换**：1.7B ↔ 0.6B 自动释放旧模型再加载新模型

---

## 📦 一键部署

### Docker 一行命令

```bash
docker run -d --gpus '"device=2"' --name qwen3-asr \
  -p 8250:8200 -p 8251:8201 \
  --restart unless-stopped \
  neosun/qwen3-asr:latest
```

打开 http://localhost:8250 即可使用！

### 或者用 docker-compose

```bash
git clone https://github.com/neosun100/Qwen3-ASR.git
cd Qwen3-ASR
bash start.sh
```

`start.sh` 会自动选择最空闲的GPU。

---

## 📡 API 使用

```bash
curl -X POST http://localhost:8250/api/transcribe \
  -F 'file=@audio.wav' \
  -F 'language=auto' \
  -F 'model=Qwen3-ASR-1.7B' \
  -F 'return_timestamps=true'
```

返回：

```json
{
  "text": "你好世界",
  "language": "Chinese",
  "timestamps": [
    {"text": "你", "start": 0.0, "end": 0.28},
    {"text": "好", "start": 0.28, "end": 0.52}
  ],
  "duration_seconds": 5.2,
  "process_time_seconds": 0.8,
  "rtf": 0.15
}
```

完整 API 文档：http://localhost:8250/docs

---

## 🔌 MCP 集成

支持 Claude Desktop / Cursor / Kiro 等 AI 工具直接调用：

```json
{
  "mcpServers": {
    "qwen3-asr": {
      "command": "python",
      "args": ["app/mcp_server.py"]
    }
  }
}
```

4个工具：`transcribe`（语音识别）、`get_status`（状态查询）、`get_languages`（语言列表）、`gpu_offload`（释放显存）

---

## 🏗️ 技术架构

| 组件 | 技术 |
|---|---|
| ASR 引擎 | Qwen3-ASR (0.6B / 1.7B) |
| 强制对齐器 | Qwen3-ForcedAligner-0.6B |
| 后端 | FastAPI + Uvicorn |
| 前端 | 纯 HTML/CSS/JS |
| MCP 服务 | fastmcp |
| 容器 | NVIDIA CUDA 12.4 + Ubuntu 22.04 |
| GPU 管理 | 懒加载 + 自动卸载 |

---

## 📊 性能数据

Qwen3-ASR 在多个基准测试中达到开源 SOTA：

| 测试集 | Qwen3-ASR-1.7B |
|---|---|
| LibriSpeech clean | WER 1.63 |
| LibriSpeech other | WER 3.38 |
| WenetSpeech net | WER 4.97 |
| WenetSpeech meeting | WER 5.88 |

此外还支持**带BGM的歌曲识别**和**歌声识别**，这是大多数ASR模型做不到的。

---

## 🌐 在线体验

**https://qwen3-asr.aws.xin**

---

## 📎 相关链接

- **GitHub**: https://github.com/neosun100/Qwen3-ASR
- **Docker Hub**: https://hub.docker.com/r/neosun/qwen3-asr
- **原始项目**: https://github.com/QwenLM/Qwen3-ASR
- **论文**: https://arxiv.org/abs/2601.21337

---

觉得有用请给个 ⭐ Star！
