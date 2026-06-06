# codex-local-doc-runtime

`docrt` 是一个面向 Windows 本机 Agent 的 DOCX/PDF/XLSX 运行时工具链，目标是在
处理本机 Word、PDF、Excel 文件时，强制走一条稳定、可诊断、可复现的链路：
`uv run docrt ...` + 本地 Microsoft Word/Excel COM。

`main` 分支定位为固定本机运行时工具链：`uv` 是主入口，缺少 `uv` 时可以通过
`winget` 自动配置；本地 Microsoft Office 是硬依赖，缺少 Word 或 Excel 时直接
返回结构化异常。Rust 仅作为可选加速。单文件 exe、便携包或 GUI 封装不属于 main。
详见
[`docs/mainline-requirements.md`](docs/mainline-requirements.md)。

当前版本定位为 **v1.1.0 stable**：适合个人长期使用、Agent 本地工具链集成和
可迁移的开源分发。v1.1 的稳定承诺覆盖 CLI 命令名、Python API、JSON 结果
基本字段、patch/task schema、错误码、日志字段、缓存清理规则和引擎调度边界。
项目不是跨平台服务器框架，也不是终端用户 exe 应用；它是 Windows + uv + 本地
Office 的固定运行时工具链。

## 能力范围

支持：

- `.docx`：读取、结构检查、安全 patch、verify、compare、通过 Word COM 导出 PDF
- `.pdf`：读取、结构检查、渲染 PNG、文本搜索、追加批注
- `.xlsx`：读取、结构检查、安全 patch、verify、compare、通过 Excel COM 导出 PDF
- `task.json`：单步或多步 Agent 任务协议
- `patch.json`：DOCX/XLSX 显式编辑协议
- `storage-report` 和 `clean`：长期使用时治理 logs、outputs、work、cache
- `analyze-logs` 和 `recent-errors`：读取历史错误日志并生成修复建议
- `repair-plan`：把历史错误聚合成下一轮优先修复计划
- `maintenance`：生成运行时健康、存储、日志分析、修复计划和状态快照
- `job-start` 和 `job-status`：后台运行低风险维护任务
- 可选 Rust core：hash、batch fingerprint、索引搜索、路径检查、JSON 预检、批量计划

不支持，且 v1.1 会用结构化错误或显式字段表达：

- OCR：图片型 PDF 会返回 `needs_ocr=true`，内置 OCR 不可用。
- `.doc`：返回 `UNSUPPORTED_LEGACY_FORMAT`，需要先转换成 `.docx`。
- `.xls`：返回 `UNSUPPORTED_LEGACY_FORMAT`，需要先转换成 `.xlsx`。
- 加密 Office/PDF 文件：返回 `ENCRYPTED_FILE_UNSUPPORTED`，不在日志中记录密码。
- 需要人工点击确认的 Office 弹窗流程：不支持隐私协议、宏安全、损坏恢复等交互弹窗。
- 复杂 PDF 原文内容编辑：只支持读取、搜索、渲染和追加批注。

重要限制：

- Word/Excel COM 是 main 主链路硬依赖，必须安装 Microsoft Word 和 Microsoft
  Excel 桌面版。
- 没有安装 Word 或 Excel 时，文档处理命令会返回结构化异常；当前不做 no-Office
  fallback。
- GitHub Actions 不假设存在桌面版 Office，因此 Office 成功链路需要本机或
  self-hosted Windows runner 验证。
- GitHub Release 会构建 Windows Rust extension wheel；从源码 clone 时如果未安装 wheel，
  仍会自动 fallback 到 Python core。
- 已用 Windows 临时目录做过 clean clone 模拟演练；迁移到目标机器后仍建议重新执行
  `doctor --agent --office-smoke` 验证本机 Office COM 和 Poppler 状态。

## 架构风险和不适用场景

`docrt` v1.1 依赖 Microsoft Office COM。Office COM 是桌面 GUI 自动化接口，
不是为高并发、无人值守服务器设计的后台文档服务。Word/Excel 弹窗、激活提示、
宏安全警告、损坏修复提示或文件锁都可能导致自动化挂起。

v1.1 通过 `doctor`、timeout、结构化错误、日志和 Office 进程清理降低风险，
但不能彻底消除 Office COM 的脆弱性。生产使用时建议把文档处理任务串行化，
或限制为低并发，并运行在可人工维护的 Windows 本机、开发机或专用 RPA 虚拟机上。

不建议把 v1.1 直接作为 SaaS 后端、Docker 服务、Linux/macOS 服务、高并发批处理平台
或无人值守文档转换集群使用。需要这些能力时，应在后续版本引入多后端 fallback、
队列隔离、LibreOffice/headless 引擎或纯 Python/Rust 只读降级链路。

## v1.1 支持矩阵

| 能力 | Windows + uv + Office | Windows 无 Office | Linux/macOS 源码运行 | Docker/服务器 |
| --- | --- | --- | --- | --- |
| `doctor` / `agent-config` | 支持 | 可诊断为未就绪 | 不作为主目标 | 不作为主目标 |
| DOCX 读取/inspect | 支持 | 不支持 | 不支持 | 不支持 |
| DOCX patch/verify/compare | 支持 | 不支持 | 不支持 | 不支持 |
| DOCX 转 PDF | 支持 | 不支持 | 不支持 | 不支持 |
| PDF 读取/search/render/annotate | 支持 | 不支持 | 不支持 | 不支持 |
| 图片型 PDF OCR | 不支持 | 不支持 | 不支持 | 不支持 |
| PDF 原文复杂编辑 | 不支持 | 不支持 | 不支持 | 不支持 |
| XLSX 读取/inspect | 支持 | 不支持 | 不支持 | 不支持 |
| XLSX patch/verify/compare | 支持 | 不支持 | 不支持 | 不支持 |
| XLSX 转 PDF | 支持 | 不支持 | 不支持 | 不支持 |
| 后台维护、日志、repair-plan | 支持 | 可用但文档处理未就绪 | 不作为主目标 | 不作为主目标 |
| Rust 加速 | Release wheel 或本机构建 | 可构建但主链路未就绪 | 源码构建 | 源码构建 |

main 的正式目标环境是 Windows + PowerShell + uv + Microsoft Word + Microsoft
Excel。`.venv\Scripts\docrt.exe` 只是 uv 管理的虚拟环境内部启动器，不是 main 线
交付物。

## 环境要求

本机 Agent 主链路必须存在：

- Git，用于从仓库恢复源码运行时
- uv，用于源码恢复、运行、开发验证和 CI；缺少时可由 docrt bootstrap/doctor 链路
  通过 winget 自动配置
- Microsoft Word 桌面版
- Microsoft Excel 桌面版
- Windows 10/11 + PowerShell
- 可联网安装依赖

main 分支不交付单文件 exe、便携 exe 或 GUI 包装器。`.venv\Scripts\docrt.exe`
只属于 uv 管理的虚拟环境内部实现细节，不能脱离 `.venv` 和项目目录单独复制使用。

Office/PDF 增强能力：

- Microsoft Word：用于 `docx-to-pdf`
- Microsoft Excel：用于 `xlsx-to-pdf`
- Poppler：用于额外 PDF 诊断和渲染工具检查

Rust 加速可选：

- Rust toolchain
- cargo
- maturin，已放在 dev 依赖中

安装基础工具：

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

安装 Rust 可选工具：

```powershell
winget install --id Rustlang.Rustup -e
```

安装后如果 `git`、`uv` 或 `cargo` 不能立即识别，重启 PowerShell。

## Clone 后恢复使用

推荐固定路径：

```powershell
Set-Location D:\project\python
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
```

如果不需要 Rust 加速，到这里即可使用；Rust 缺失只影响加速，不放宽 `uv + Office`
主链路要求。

## 运行入口

v1.1 的主线源码入口是 `uv run docrt ...`，因为它能保证源码恢复、依赖同步和开发验证
可复现。Agent 内部可以调用这些命令，普通用户只应看到自然语言需求和结果文件：

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt version
uv run docrt doctor --agent --office-smoke
```

如果当前 PowerShell 里完全没有 `uv`，先运行仓库级 bootstrap 脚本；它只安装/检查
`uv`，不打包 exe，也不绕开本地 Office 要求：

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
.\scripts\bootstrap-uv.ps1
```

exe、便携包、安装器或 GUI 封装属于独立 branch 方案，不能反向改变 main 线定位。
main 分支不把“全局 python 直接运行”作为用户路径；Python API 和 `.venv` 内启动器
服务于开发、测试和上层封装，用户主路径仍固定为 `uv run docrt ...`。

启用本机 Rust 加速：

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
$env:PYO3_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
$pythonBase = (& $env:PYO3_PYTHON -c "import sys; print(sys.base_prefix)").Trim()
$env:PATH = "$pythonBase;$env:PATH"
uv run maturin develop --manifest-path crates\docrt-core\Cargo.toml
uv run docrt doctor --agent
```

看到以下字段表示 Rust 已启用：

```json
{
  "core": {
    "backend": "rust",
    "rust_available": true
  }
}
```

## Codex 集成

生成可复制到 `AGENTS.md` 的配置片段：

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt agent-config
```

建议写入全局或项目级 `AGENTS.md` 的核心规则：

```text
When working with local .docx, .pdf, or .xlsx files on Windows, prefer
docrt from D:\project\python\codex-local-doc-runtime.

Before processing documents:

Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --agent --office-smoke

Use docrt read/patch/verify/render/search commands instead of ad hoc scripts.
Do not assume OCR, .doc, .xls, encrypted Office files, interactive Office dialogs,
or complex PDF original-content editing are supported.
```

仓库中也提供模板：

```powershell
Get-Content examples\AGENTS.template.md
```

## 常用命令

环境检查：

```powershell
uv run docrt version
uv run docrt doctor
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
```

DOCX：

```powershell
uv run docrt inspect-docx path\to\file.docx
uv run docrt read-docx path\to\file.docx --output outputs\file.docx.read.json
uv run docrt validate-patch path\to\patch.json
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx --dry-run
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx
uv run docrt verify-docx path\to\file.docx outputs\file.patched.docx --expect path\to\patch.json
uv run docrt compare-docx path\to\file.docx outputs\file.patched.docx
uv run docrt docx-to-pdf path\to\file.docx outputs\file.pdf
```

PDF：

```powershell
uv run docrt inspect-pdf path\to\file.pdf
uv run docrt read-pdf path\to\file.pdf --output outputs\file.pdf.read.json
uv run docrt read-pdf path\to\file.pdf --pages 1,3-5
uv run docrt search-pdf path\to\file.pdf "keyword"
uv run docrt search-pdf path\to\file.pdf "keyword" --pages 1-10
uv run docrt render-pdf path\to\file.pdf outputs\file-pages
uv run docrt render-pdf path\to\file.pdf outputs\file-pages --pages 2
uv run docrt annotate-pdf path\to\file.pdf path\to\annotations.json outputs\file.annotated.pdf
```

XLSX：

```powershell
uv run docrt inspect-xlsx path\to\file.xlsx
uv run docrt read-xlsx path\to\file.xlsx --output outputs\file.xlsx.read.json
uv run docrt validate-patch path\to\patch.json
uv run docrt patch-xlsx path\to\file.xlsx path\to\patch.json outputs\file.patched.xlsx --dry-run
uv run docrt patch-xlsx path\to\file.xlsx path\to\patch.json outputs\file.patched.xlsx
uv run docrt verify-xlsx path\to\file.xlsx outputs\file.patched.xlsx --expect path\to\patch.json
uv run docrt compare-xlsx path\to\file.xlsx outputs\file.patched.xlsx
uv run docrt xlsx-to-pdf path\to\file.xlsx outputs\file.pdf
```

批量、索引和缓存：

```powershell
uv run docrt fingerprint path\to\file.docx
uv run docrt batch-fingerprint path\to\a.docx path\to\b.xlsx
uv run docrt cache-read path\to\file.docx
uv run docrt batch-read path\to\a.docx path\to\b.pdf --use-cache
uv run docrt batch-inspect path\to\a.docx path\to\b.xlsx
uv run docrt index path\to\a.docx path\to\b.xlsx
uv run docrt search "keyword"
```

`batch-read` 返回读取内容并可使用 `--use-cache`；`batch-inspect` 返回结构检查结果，
不使用 read cache。两者都会隔离单文件失败，返回 `success_count`、`failed_count`
和每个文件的 `ok/error`，不会因为其中一个文件缺失就中断整批。

日志分析与修复建议：

```powershell
uv run docrt analyze-logs
uv run docrt analyze-logs --days 30 --limit 200
uv run docrt recent-errors --limit 20
uv run docrt repair-plan --days 30
uv run docrt maintenance
```

`repair-plan` 会读取最近错误日志，按严重程度、出现次数和修复风险生成下一轮开发优先级，
并默认写入 `state\repair-plan.latest.json`。它只生成计划，不自动修改核心逻辑。
如果某个操作在最后一次错误之后已经有成功运行，计划项会标记
`status: observed_recovered`、记录 `last_success_at`，并降级为 `P4` 继续观察，
避免历史 smoke 失败反复干扰下一轮开发。
`maintenance` 也会生成同一份修复计划快照，适合作为每轮开发前的入口命令。

后台维护任务：

```powershell
uv run docrt job-start maintenance
uv run docrt job-start analyze-logs --days 30
uv run docrt job-start repair-plan --days 30
uv run docrt job-start clean-retention
uv run docrt job-status <job-id>
```

`job-start clean-retention` 默认只做后台 dry-run；如果确认要删除过期日志、诊断和缓存，
使用 `uv run docrt job-start clean-retention --yes`。

当前后台任务只用于低风险维护任务。DOCX/PDF/XLSX 核心读取、编辑、转换仍建议先走前台
JSON 命令，避免用户不知道后台任务是否已经改动文档。

任务协议：

```powershell
uv run docrt validate-task path\to\task.json
uv run docrt explain-task path\to\task.json
uv run docrt run-task path\to\task.json
uv run docrt validate-result path\to\result.json
```

`explain-task` 会区分 `supports_native_dry_run` 与计划模式 dry-run。当前只有
`patch-docx` 和 `patch-xlsx` 是原生 dry-run，其他任务的 dry-run 是“只解释计划，不执行”。

## 安全编辑闭环

DOCX 和 XLSX 修改都要求显式 `patch.json`，不会默认覆盖原文件。

推荐链路：

```powershell
uv run docrt read-docx path\to\file.docx --output outputs\before.json
uv run docrt validate-patch path\to\patch.json
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx --dry-run
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx
uv run docrt verify-docx path\to\file.docx outputs\file.patched.docx --expect path\to\patch.json
uv run docrt compare-docx path\to\file.docx outputs\file.patched.docx
```

DOCX 当前支持：

- `replace_text`：按文本替换，可限制段落、表格或全部范围
- `replace_paragraph`：按段落索引替换
- `replace_heading`：按标题文本、标题样式或两者组合替换
- `replace_table_cell`：按表格、行、列定位替换单元格

DOCX 格式保留采用尽力策略：`replace_text` 在匹配文本位于单个 run 时保留该 run
格式；`replace_paragraph`、`replace_heading` 和 `replace_table_cell` 会保留段落样式和
首个 run 的基础格式。复杂跨 run 的替换仍可能改变局部行内样式，排版敏感场景应在
patch 后执行 `compare-docx`。

`read-xlsx` 默认预览每个 sheet 的前 20 行 x 20 列，并在 JSON 中通过
`metadata.sheets[].preview_truncated` 和 `warnings` 标记是否被截断。需要完整数据时，
应使用明确的 range/task 设计，避免把预览结果误认为全量 workbook。

XLSX patch 当前支持：

- `set_cell`
- `set_range_values`
- `add_sheet`
- `rename_sheet`

XLSX 值修改会保留目标单元格已有样式和数字格式，并在 patch result 中标记
`format_preservation=preserve_existing_cell_style`。新增 sheet 使用 openpyxl 默认样式；
复杂图表、透视表、宏和外部链接不作为 patch 保真目标。

PDF 当前只承诺读取、渲染、搜索和追加批注，不承诺复杂原文编辑。

## 运行产物和清理

默认运行产物：

```text
logs/
outputs/
work/
outputs/diagnostics/
work/cache/
state/
```

这些目录都已加入 `.gitignore`，不会污染仓库提交。

查看占用：

```powershell
uv run docrt storage-report
```

清理预览，默认不会删除：

```powershell
uv run docrt clean --logs --work --cache
uv run docrt clean --retention
```

默认只输出摘要，避免长期使用后刷出大量文件路径。如果需要查看具体文件列表：

```powershell
uv run docrt clean --logs --work --cache --verbose
uv run docrt clean --retention --verbose
```

确认删除：

```powershell
uv run docrt clean --logs --work --cache --yes
uv run docrt clean --retention --yes
```

按时间手动清理：

```powershell
uv run docrt clean --logs --work --cache --older-than 14 --yes
```

`--retention` 会使用 `docrt.config.json` 中的 `log_retention_days`、
`diagnostic_retention_days` 和 `cache_retention_days`。默认只覆盖 logs、
diagnostics 和 cache，不会自动清理 outputs 里的导出文件。

清理 outputs 时要更谨慎，因为里面可能有你希望保留的导出文件：

```powershell
uv run docrt clean --outputs --older-than 30 --yes
```

## 输出协议

所有 CLI 命令都向 stdout 输出 JSON，并写入结构化日志。普通运行日志写入
`logs/{run_id}.jsonl`，失败事件额外写入 `logs/errors/YYYY-MM-DD.error.jsonl`，
诊断报告写入 `outputs/diagnostics/{run_id}.diagnostic.json`。

日志写入采用降级策略：如果日志目录不可写，命令会尽量继续返回标准 JSON，不让日志
系统本身中断文档处理。

标准结果形状：

```json
{
  "ok": true,
  "operation": "doctor",
  "input_path": null,
  "output_path": null,
  "backend": "doctor",
  "run_id": "20260605-120000-abcdef",
  "started_at": "2026-06-05T12:00:00.000Z",
  "ended_at": "2026-06-05T12:00:00.100Z",
  "duration_ms": 100,
  "error_code": null,
  "error_message": null,
  "exception_type": null,
  "traceback": null,
  "recovery_actions": [],
  "diagnostic_report_path": null,
  "log_path": "logs/run.jsonl",
  "data": {}
}
```

失败时优先看：

- `error_code`
- `error_message`
- `exception_type`
- `recovery_actions`
- `diagnostic_report_path`
- `log_path`

## Clean Clone 演练

可以用临时目录模拟一台新机器的 clone 安装。v1.1 的文档处理链路要求
`uv run docrt ...` 和本地 Word/Excel COM；这套演练必须把
`doctor --agent --office-smoke` 作为验收的一部分。

```powershell
$cloneRoot = Join-Path $env:TEMP "docrt-clean-clone"
Remove-Item -Recurse -Force $cloneRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $cloneRoot | Out-Null
Set-Location $cloneRoot
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
Set-Location .\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
uv run docrt read-docx examples\fixtures\sample.docx
uv run docrt search-pdf examples\fixtures\sample.pdf "sample"
uv run docrt storage-report
```

如果这一步报告 `OFFICE_COM_REQUIRED`、`WORD_COM_UNAVAILABLE` 或
`EXCEL_COM_UNAVAILABLE`，说明当前机器不满足 mainline 运行时要求；v1.1 当前不会尝试
no-Office fallback。

## 开发验证

Python：

```powershell
uv sync --dev
uv run ruff format .
uv run ruff check .
uv run pytest
uv run pytest --cov=docrt
```

Rust：

```powershell
$env:PYO3_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
$pythonBase = (& $env:PYO3_PYTHON -c "import sys; print(sys.base_prefix)").Trim()
$env:PATH = "$pythonBase;$env:PATH"
cargo fmt --check --manifest-path crates\docrt-core\Cargo.toml
cargo clippy --manifest-path crates\docrt-core\Cargo.toml -- -D warnings
cargo test --manifest-path crates\docrt-core\Cargo.toml
uv run maturin develop --manifest-path crates\docrt-core\Cargo.toml
```

本地最终验收：

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run ruff format .
uv run ruff check .
uv run pytest
uv run docrt doctor
uv run docrt doctor --agent
uv run docrt agent-config
uv run docrt storage-report
uv run docrt clean --retention
uv run docrt analyze-logs
uv run docrt repair-plan
uv run docrt maintenance
```

## CI

GitHub Actions 只验证源码质量、Rust 构建、Python fallback 单元测试和 Office 缺失时的
结构化边界。GitHub hosted runner 通常没有桌面版 Word/Excel，因此不能代表完整 mainline
文档处理验收。

当前覆盖：

- `uv sync --dev`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`
- `uv run pytest --cov=docrt`
- `cargo fmt --check`
- `cargo clippy -- -D warnings`
- `cargo test`
- `uv run maturin develop`
- mocked runtime preflight and missing-Office structured-error tests

完整验收必须在安装了 Word/Excel 的 Windows 本机运行：

```powershell
uv run docrt doctor --agent --office-smoke
uv run pytest
```

## Release

v1.1 使用 git tag 触发发布：

```powershell
git tag v1.1.0
git push origin main --tags
```

`.github/workflows/release.yml` 会在 Windows 上运行完整质量门禁，构建 Python 包和
Windows Rust extension wheel，并上传到 GitHub Release。普通 clone 使用不依赖 Rust
wheel；没有原生扩展时会自动走 Python fallback。

## 项目结构

```text
codex-local-doc-runtime/
  .github/workflows/ci.yml
  crates/docrt-core/
  docs/
    adr/
    architecture.md
    patch-protocol.md
    task-manifest.md
  examples/
  schemas/
  src/docrt/
  tests/
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  README.md
  SECURITY.md
  pyproject.toml
  uv.lock
```

## 相关文档

- `docs/quickstart.md`：clone 后 5 条命令完成最小可用验证
- `docs/release-notes-1.1.0.md`：v1.1.0 发布说明、破坏性变化和验证记录
- `docs/codex-integration.md`：Codex/Agent 集成规则
- `docs/patch-protocol.md`：DOCX/XLSX patch 协议
- `docs/task-manifest.md`：Agent task 协议
- `docs/pdf-annotation.md`：PDF 追加批注协议
- `docs/storage-management.md`：缓存和中间产物清理
- `docs/troubleshooting.md`：错误恢复建议
- `docs/v1-support-boundaries.md`：v1.1 支持矩阵、限制和正式边界
- `docs/adr/`：架构决策记录

## License

MIT
