# Mainline Requirements: uv + Local Office Runtime Toolchain

本文固定 `main` 分支的 v1.1 架构方向：`docrt` 是 Windows 本机文档运行时工具链，
不是单文件 exe，也不是跨平台 headless SDK。

## 定位

`main` 分支强制采用：

```text
PowerShell / Agent
  -> uv run docrt ...
     -> local Microsoft Word / Excel COM preflight
        -> DOCX / PDF / XLSX processing
        -> optional Rust acceleration
```

核心目标是让 Codex / Agent 在用户本机使用统一、可诊断、可复现的链路处理
`.docx`、`.pdf`、`.xlsx`，而不是让调用方自由选择环境。

## 硬约束

- 必须通过 `uv run docrt ...` 运行主链路。
- 如果缺少 `uv`，运行时可以通过 `scripts\bootstrap-uv.ps1` 或
  `winget install --id astral-sh.uv -e` 自动配置。
- 必须存在本地 Microsoft Word 和 Microsoft Excel COM。
- 如果缺少本地 Office，直接返回结构化异常；当前不实现 no-Office fallback。
- Rust core 仅作为可选加速层；没有 Rust 扩展时必须 fallback 到 Python core。
- main 不交付单文件 exe、GUI/TUI、PyInstaller/Nuitka 打包产物。

## Office 边界

本地 Office 是主链路的强依赖，不只是转 PDF 时才需要。

原因：

- Word/Excel 是用户本机文档真实渲染与兼容性的权威来源。
- Agent 工作流需要统一环境前置条件，而不是在不同机器上隐式降级。
- 没有 Office 时当前阶段直接暴露异常，后续再单独设计 fallback。

Office 缺失时允许返回：

- `OFFICE_COM_REQUIRED`
- `WORD_COM_UNAVAILABLE`
- `EXCEL_COM_UNAVAILABLE`

## uv 边界

`uv` 是主链路入口，不只是推荐工具。

允许行为：

- 检测 `uv` 是否可用。
- 缺少 `uv` 时尝试通过 `winget` 自动安装。
- 自动安装失败时返回结构化异常。

源码仓库级自举入口：

```powershell
.\scripts\bootstrap-uv.ps1
```

已经能启动 `docrt` 时的 CLI 检查入口：

```powershell
uv run docrt bootstrap-uv
```

相关错误：

- `UV_UNAVAILABLE`
- `UV_BOOTSTRAP_FAILED`

## 内部处理实现

Office 是外部运行时前置条件；具体读写仍可以使用 Python 库实现：

- `.docx`：`python-docx` 读取、检查、patch、verify、compare。
- `.pdf`：PyMuPDF 读取、检查、搜索、渲染、批注。
- `.xlsx`：`openpyxl` / `pandas` 读取、检查、patch、verify、compare。
- DOCX/XLSX 高保真 PDF 导出：Word / Excel COM。

这些 Python 库是内部实现细节，不代表无 Office fallback。

## Rust 边界

Rust 不接管业务调度，只做可选加速：

- 批量 fingerprint。
- 大目录遍历。
- 大文本搜索。
- 索引查询。
- OOXML ZIP 结构预扫描。
- JSON manifest 预检。

Rust extension 缺失时走 Python fallback。

## v1.1 验收清单

文档验收：

- README 明确主链路是 `uv + local Office`。
- README 明确缺 uv 会尝试自动配置。
- 源码仓库存在不依赖 `uv run` 的 `scripts\bootstrap-uv.ps1` 自举入口。
- README 明确缺 Office 直接结构化失败，当前无 fallback。
- docs 不再把 Office 描述成可选高保真能力。
- exe / GUI / PyInstaller / Nuitka 仍不属于 main。

代码验收：

- 存在 uv 检测和 bootstrap 逻辑。
- 文档处理 API / CLI / task manifest 进入处理前检查 uv 和 Word/Excel COM。
- `doctor --agent` 把 uv、Word COM、Excel COM 作为 required。
- 缺 Office 返回结构化错误。
- Rust core 可用时加速，不可用时 Python fallback。

测试验收：

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run docrt doctor --agent --office-smoke
```
