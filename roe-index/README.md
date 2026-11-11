# Rivne address index

Address → outage sub-queue index for the Svitlo apps, built from Rivneoblenergo's two GPV documents
linked on https://www.roe.vsei.ua/disconnections:

- `GPV_cherga_misto_Rivne*.pdf` — the city of Rivne: `№ | streets and houses | sub-queue`;
- `GPV_cherga_Rivnenska_oblast*.pdf` — the rest of the region: `hromada | settlements | streets and houses | queue`.

The operator has no address search, so the apps look the address up in this index on the device.
Nothing is sent anywhere. The format is the one of [`../gpv-index`](../gpv-index) (Poltava), and the
apps use the same lookup for both.

## Pipeline

1. `tools/pdflines.swift` — text lines with coordinates (PDFKit, macOS; copy of gpv-index's).
2. `tools/pdfrules.swift` — horizontal table rules (CoreGraphics content stream: `re`, `m`/`l` with the CTM).
   Rows can't be told apart by text spacing alone (the city table's line gap equals its row gap).
3. `tools/roe_rows.py` — a row is the band between two rules crossing the queue column; lines go to the
   band holding their middle, columns by x. A band without a queue continues the row above.
4. `tools/build.py` — row text → entries with gpv-index's `gpv_parse`, plus Rivne-specific fixes:
   "(повністю)" dropped, "с.Бабин -- Тиха, Заводська" read as streets, "С.Хороброго" (a street) not
   taken for a settlement, and a "settlement" that the settlements column never names is a street.
   Every settlement of the settlements column gets a whole-settlement entry (partial if marked "частково"
   or if the row lists some of its streets). Validates and writes `index.json`, `meta.json`, `report.json`.
5. `tools/find_source.py` — the current links on the disconnections page.

```
python3 roe-index/tools/build.py --city-pdf CITY.pdf --region-pdf REGION.pdf \
    --city-url URL --region-url URL --out roe-index --previous roe-index/index.json --work TMP
python3 -m unittest discover -s roe-index/tests
```

`.github/workflows/roe-index.yml` runs this daily on the self-hosted Mac runner (`svitlo-ua`) and commits
the index when either document changes; a failure keeps the old index and opens one issue.

## index.json

As in gpv-index: `rows` (`q`, `branch` = hromada, `text` = source text shown as evidence) and
`entries` `[settlement, street|null, kind, houses|null, partial 0/1, row]`. `source` has `url` / `sha256`
for the region document and `city_url` / `city_sha256` for the city one.

Known limits: some cells list organisations or districts ("район Басів кут") rather than streets; those
match only by settlement. The same address may be listed in several sub-queues: the apps show all.
