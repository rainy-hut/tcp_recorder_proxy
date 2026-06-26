# TCP 命令码流录制代理器

一个独立的 PySide6 桌面工具，用于透明 TCP 转发、原始码流录制、协议分类和 TOML 导出。

## 运行

```bash
python -m pip install -r requirements.txt
python run.py
```

## Windows 打包

在 Windows 命令行执行：

```bat
build_windows.bat
```

## 关键原则

- 转发优先，收到 bytes 后立即原样转发。
- 原始 `.bin` 与 `events.jsonl` 是唯一事实源。
- 协议解析、SQLite、TOML 导出均为可重新生成的派生产物。
- BBU 同一端口允许 MML 文本、F634 承载 MML、BBU Binary 与未知帧混合出现。
