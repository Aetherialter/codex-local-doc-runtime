# codex-local-doc-runtime

`docrt` 是一个面向 Windows + PowerShell + uv 的本地文档运行时，目标是让
Codex 或其他 Agent 在处理本机 Word、PDF、Excel 文件时，优先走一套稳定、
可诊断、可复现的命令链路，而不是临时脚本或不稳定的默认能力。

当前版本定位为 **lead preview**：适合个人长期使用和开源预览，但还不是
`v1.0.0`。项目已经支持 clone 后恢复使用、Agent 配置片段生成、JSON CLI
协议、安全编辑闭环、缓存治理和可选 Rust 加速。

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

不支持：

- OCR
- `.doc`
- `.xls`
- 加密 Office 文件
- 需要人工点击确认的 Office 弹窗流程
- 复杂 PDF 原文内容编辑

重要限制：

- Word/Excel COM 能力依赖本机安装 Microsoft Word 和 Microsoft Excel。
- 没有安装 Word 时，`docx-to-pdf` 和 Word COM smoke 会不可用。
- 没有安装 Excel 时，`xlsx-to-pdf` 和 Excel COM smoke 会不可用。
- GitHub Actions 不假设存在桌面版 Office，因此 CI 只覆盖非交互能力。
- Rust 加速已经可用，但当前没有发布预编译 wheel。别人 clone 后如果需要 Rust 加速，
  需要本机安装 Rust toolchain 并运行 `maturin develop`；否则自动 fallback 到 Python。
- 已用 Windows 临时目录做过 clean clone 模拟演练；迁移到目标机器后仍建议重新执行
  `doctor --agent --office-smoke` 验证本机 Office COM 和 Poppler 状态。

## 环境要求

基础使用必须存在：

- Windows 10/11
- PowerShell
- Git
- uv
- 可联网安装依赖

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

如果只需要 Python fallback，不需要 Rust 加速，到这里即可使用。

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
`maintenance` 也会生成同一份修复计划快照，适合作为每轮开发前的入口命令。

后台维护任务：

```powershell
uv run docrt job-start maintenance
uv run docrt job-start analyze-logs --days 30
uv run docrt job-start repair-plan --days 30
uv run docrt job-status <job-id>
```

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

XLSX 当前支持：

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
```

默认只输出摘要，避免长期使用后刷出大量文件路径。如果需要查看具体文件列表：

```powershell
uv run docrt clean --logs --work --cache --verbose
```

确认删除：

```powershell
uv run docrt clean --logs --work --cache --yes
```

按时间清理：

```powershell
uv run docrt clean --logs --work --cache --older-than 14 --yes
```

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

可以用临时目录模拟一台新机器的 clone 安装。本预览版已用该链路验证过基础
Python fallback 能力；目标机器仍需要按实际环境复查 Office COM。

```powershell
$cloneRoot = Join-Path $env:TEMP "docrt-clean-clone"
Remove-Item -Recurse -Force $cloneRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $cloneRoot | Out-Null
Set-Location $cloneRoot
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
Set-Location .\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent
uv run docrt agent-config
uv run docrt read-docx examples\fixtures\sample.docx
uv run docrt search-pdf examples\fixtures\sample.pdf "sample"
uv run docrt storage-report
```

这套演练不会证明 Word/Excel COM 可用。Office COM 必须在目标机器上安装 Word/Excel 后执行：

```powershell
uv run docrt doctor --agent --office-smoke
```

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
uv run docrt clean --logs --work --cache
uv run docrt analyze-logs
uv run docrt repair-plan
uv run docrt maintenance
```

## CI

GitHub Actions 使用 `windows-latest`，当前覆盖：

- `uv sync --dev`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`
- `uv run pytest --cov=docrt`
- `cargo fmt --check`
- `cargo clippy -- -D warnings`
- `cargo test`
- `uv run maturin develop`
- CLI smoke

CI 不验证桌面版 Word/Excel COM。需要在本机运行 `doctor --agent --office-smoke`。

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

- `docs/codex-integration.md`：Codex/Agent 集成规则
- `docs/patch-protocol.md`：DOCX/XLSX patch 协议
- `docs/task-manifest.md`：Agent task 协议
- `docs/pdf-annotation.md`：PDF 追加批注协议
- `docs/storage-management.md`：缓存和中间产物清理
- `docs/troubleshooting.md`：错误恢复建议
- `docs/adr/`：架构决策记录

## License

MIT
