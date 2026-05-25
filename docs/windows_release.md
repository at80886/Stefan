# Windows 发布说明

当前项目使用 PyInstaller 生成 Windows 10/11 x64 发布目录。

## 构建环境

- 使用 `D:\Anaconda\envs\py39\python.exe`。
- Python 环境需要包含 PyQt6 和 PyInstaller。
- 构建脚本会检查 64 位 Python，并默认运行项目测试。

## 构建命令

在项目根目录执行：

```powershell
.\scripts\build_windows.ps1
```

如需指定 Python：

```powershell
.\scripts\build_windows.ps1 -Python D:\Anaconda\envs\py39\python.exe
```

## 发布产物

- 发布目录：`dist/StefanSimulator/`
- 启动程序：`dist/StefanSimulator/StefanSimulator.exe`
- 分发压缩包：`dist/StefanSimulator-win10-win11-x64.zip`

发布目录中包含应用运行所需的 Python 运行库、PyQt6 组件、样式文件和示例参数文件。分发时应保留整个 `StefanSimulator` 目录结构。

## 资源路径

应用在源码运行时读取项目根目录下的 `resources/`。发布运行时读取 PyInstaller 打包到程序内部目录的 `resources/`，因此无需手工复制样式或示例参数。
