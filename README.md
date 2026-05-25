# 一维 Stefan 问题模拟应用

本项目用于开发一款基于 PyQt6 的 Windows 桌面应用，支持一维 Stefan 问题的参数配置、数值模拟、过程可视化和结果导出。

## AI利用说明

- 本项目基于 Codex + ChatGPT-5.5 开发。

## 项目资源框架

- `src/stefan_app/`：应用源码包，包含入口、界面、模型、求解、绘图、导出和通用工具模块。
- `resources/`：应用静态资源，包含样式、图标占位和示例参数。
- `tests/`：测试资源，用于验证基础模块可导入、资源路径有效和后续核心功能行为。
- `docs/`：非任务类技术说明文档。
- `.vscode/`：VSCode 项目级共享配置。
- `pyproject.toml`、`requirements.txt`、`environment.yml`：Python 包、pip 依赖和 conda 环境资源。

## 当前状态

当前阶段已建立项目资源框架，后续功能开发应在既有模块边界内逐步扩展。

## Windows 发布

Win10/11 x64 发布流程见 `docs/windows_release.md`。

在项目根目录执行：

```powershell
.\scripts\build_windows.ps1
```

发布目录为 `dist/StefanSimulator/`，启动程序为 `dist/StefanSimulator/StefanSimulator.exe`。
