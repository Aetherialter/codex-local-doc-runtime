# PDF Annotation

`annotate-pdf` adds safe PDF annotations to a copy of a PDF. It does not edit
the original PDF text stream.

```powershell
uv run docrt annotate-pdf input.pdf annotations.json output.pdf
```

Supported annotation types:

- `highlight`: requires `page_number` and `bbox`.
- `rectangle`: requires `page_number` and `bbox`.
- `text_note`: requires `page_number`, `point`, and `text`.
- `stamp`: requires `page_number`, `point`, and `text`.

Example:

```json
{
  "annotations": [
    {
      "type": "rectangle",
      "page_number": 1,
      "bbox": [60, 55, 180, 90]
    },
    {
      "type": "text_note",
      "page_number": 1,
      "point": [72, 120],
      "text": "Review"
    }
  ]
}
```

PDF OCR and complex original-content editing are outside the current scope.
