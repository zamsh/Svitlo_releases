# GPV address index

Address → outage sub-queue index for the Svitlo apps, built from the official
Poltavaoblenergo document "Графік погодинного відключення електроенергії" (PDF on
https://www.poe.pl.ua/disconnection/hrafik-pohodynnoho-vidkliuchennia-elektroenerhii/).

The site's own address search returns no queue for most addresses ("several connections"),
so the apps look the address up in this index on the device. Nothing is sent anywhere.

## Pipeline

1. `tools/pdflines.swift` — text lines with coordinates (PDFKit, macOS only: other extractors
   return this document in the wrong reading order).
2. `tools/gpv_rows.py` — rebuilds table rows: queue section, branch, row number, text.
3. `tools/gpv_parse.py` — row text → settlements, streets, houses (lists, ranges, odd/even, "partially").
4. `tools/build.py` — builds `index.json` + `meta.json`, validates the result, writes `report.json`.
5. `tools/gpv_lookup.py` — reference lookup (the apps port it): house → range → whole street → whole settlement.

```
python3 tools/build.py --pdf HPV.pdf --source-url URL --out . --previous index.json
python3 -m unittest discover -s tests
```

## index.json

```
{"version": 1,
 "source": {"url", "sha256", "valid_from", "valid_to", "generated_at"},
 "rows": [{"q": "5.1", "branch": "...", "text": "source row text"}],
 "entries": [[settlement, street|null, kind, houses|null, partial 0/1, row]]}
```

`houses` items are `"18"`, `"21/6"`, `"15а"` or ranges `[from, to]` / `[from, to, "odd"|"even"]`.
An address may legitimately appear in several sub-queues (several connections): the apps show all.
