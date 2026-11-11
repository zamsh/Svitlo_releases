# Kharkiv address index

Address → outage sub-queue index for the Svitlo apps, built from Kharkivoblenergo's
"Адреси та черги" PDF (`Адреси та черги 26-27.pdf` for the 2026–27 season), found through the site's
file API on https://oblenergo.kharkiv.ua.

The document is one table: `addresses | 1 черга (І, ІІ) | … | 6 черга (І, ІІ)`, with an "X" in the
row's sub-queue column ("1 черга, ІІ" = 1.2). The operator has no address search, so the apps look the
address up in this index on the device. Nothing is sent anywhere. The format is the one of
[`../gpv-index`](../gpv-index) (Poltava), and the apps use the same lookup.

## Pipeline

1. `tools/pdflines.swift`, `tools/pdfrules.swift` — text lines with coordinates and horizontal table rules
   (copies of roe-index's; PDFKit / CoreGraphics, macOS).
2. `tools/kh_rows.py` — a row is the band between two rules; its sub-queue is the column of its "X"
   (column centres from the header's "І ІІ" cells). PDFKit often glues the X to the row's last text line.
3. `tools/kh_text.py` — most cells name things marker-last ("Валки м., Харківська вул.; Гузівка с.");
   they are rewritten marker-first for gpv-index's `gpv_parse`. Also fixes typing slips: glued words
   ("ЗміївАдминистративна"), "с.Лиман:Садова" (that settlement's streets), "х." / "г." / "п." / "ул." / "пер.".
   Districts ("Валківський р-н") are taken out of the text that is parsed.
4. `tools/build.py` — entries, validation, `index.json`, `meta.json`, `report.json`. Bands of the same
   sub-queue that continue a cell are merged; enterprises without a settlement are left out.
5. `tools/find_source.py` — the current document's link.

```
python3 khoe-index/tools/build.py --pdf DOC.pdf --url URL --out khoe-index --previous khoe-index/index.json --work TMP
python3 -m unittest discover -s khoe-index/tests
```

`.github/workflows/khoe-index.yml` runs this daily on the self-hosted Mac runner (`svitlo-ua`) and commits
the index when the document changes; a failure keeps the old index and opens one issue.

## index.json

As in gpv-index: `rows` (`q`, `branch`, `text` = source cell shown as evidence) and `entries`
`[settlement, street|null, kind, houses|null, partial 0/1, row]`. `branch` is "Харківська область" for
every row: the cells use the pre-2020 districts and don't tie each settlement to one, so the district
stays only in the row text. `source.valid_from` / `valid_to` come from the document's title.

Known limits: the document covers the region; the city of Kharkiv appears only in a few rows (mostly
enterprises). Abbreviated names stay as written ("Н.Бишкин", "Ст.Ріпки"). Same-named villages of
different districts share one picker entry; the lookup shows every sub-queue found.
