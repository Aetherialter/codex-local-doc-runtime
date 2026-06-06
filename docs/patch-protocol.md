# Patch Protocol

Patch commands apply explicit JSON operations to a copy of a document. They do
not overwrite the input file.

## DOCX Patch

Command:

```powershell
uv run docrt patch-docx input.docx patch.json output.docx
uv run docrt patch-docx input.docx patch.json output.docx --dry-run
```

Patch shape:

```json
{
  "document_type": "docx",
  "operations": [
    {
      "type": "replace_text",
      "find": "old text",
      "replace": "new text",
      "scope": "all",
      "max_replacements": 3,
      "conflict_policy": "fail"
    },
    {
      "type": "replace_paragraph",
      "paragraph_index": 0,
      "expected_text": "old paragraph",
      "text": "replacement paragraph"
    },
    {
      "type": "replace_heading",
      "heading_text": "Old heading",
      "heading_style": "Heading 1",
      "match": "exact",
      "text": "Replacement heading"
    },
    {
      "type": "replace_table_cell",
      "table_index": 0,
      "row_index": 1,
      "column_index": 0,
      "expected_text": "old cell",
      "text": "replacement cell"
    }
  ]
}
```

Supported DOCX operations:

- `replace_text`
- `replace_paragraph`
- `replace_heading`
- `replace_table_cell`

`replace_heading` targets paragraphs whose style is a heading style. Use
`heading_text`, `heading_style`, or both. `match` can be `exact` or `contains`.

DOCX formatting is preserved on a best-effort basis:

- `replace_text` preserves the matching run formatting when the matched text is
  contained in a single run.
- `replace_paragraph` and `replace_heading` preserve the paragraph style and the
  first run formatting while rewriting the paragraph text.
- `replace_table_cell` preserves the first paragraph style and first run
  formatting in the target cell.
- Complex multi-run replacements can still change inline formatting. Use
  `compare-docx` after patching when layout or inline styling matters.

## XLSX Patch

Command:

```powershell
uv run docrt patch-xlsx input.xlsx patch.json output.xlsx
uv run docrt patch-xlsx input.xlsx patch.json output.xlsx --dry-run
```

Patch shape:

```json
{
  "document_type": "xlsx",
  "operations": [
    {
      "type": "set_cell",
      "sheet": "Summary",
      "cell": "B2",
      "expected_value": "Draft",
      "value": "Ready"
    },
    {
      "type": "set_range_values",
      "sheet": "Summary",
      "start_cell": "A4",
      "expected_values": [["Name", "Value"], ["Count", 2]],
      "values": [["Name", "Value"], ["Count", 3]]
    },
    {
      "type": "add_sheet",
      "name": "Notes"
    },
    {
      "type": "rename_sheet",
      "old_name": "Notes",
      "new_name": "Review"
    }
  ]
}
```

Supported XLSX operations:

- `set_cell`
- `set_range_values`
- `add_sheet`
- `rename_sheet`

`set_cell` and `set_range_values` preserve the existing cell style and number
format when replacing values. The patch result marks these changes with
`format_preservation=preserve_existing_cell_style`. New sheets use openpyxl's
default sheet styling. Charts, pivot tables, macros, and external links are not
treated as patch fidelity targets in this preview.

## Result

Patch commands return the normal JSON result shape. The `data` field contains:

- `input_path`
- `patch_path`
- `output_path`
- `patch_summary`
- `verification`

The `verification` field is a lightweight read-back summary. For deeper checks,
run:

```powershell
uv run docrt verify-docx before.docx after.docx
uv run docrt verify-xlsx before.xlsx after.xlsx
uv run docrt verify-docx before.docx after.docx --expect patch.json
uv run docrt verify-xlsx before.xlsx after.xlsx --expect patch.json
```

Dry-run mode validates the patch, plans changes, and returns `planned_count`,
`applied_count`, `skipped_count`, and `conflicts` without writing the output
file.
