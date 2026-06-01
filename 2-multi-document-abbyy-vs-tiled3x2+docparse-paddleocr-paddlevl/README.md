# Multi-Document ABBYY vs Tiled 3x2 + Docparse PaddleOCR + PaddleVL Comparison

This folder contains a multi-document OCR comparison between:

- `ABBYY` outputs under `test-data/abbyy`
- `Paddle` outputs under `test-data/preprocessing-tiling_3x2_dp+paddleocr+vl+clean`

The Paddle side is the same general workflow used in the stress test:

- preprocessing
- `3x2` tiling with docparse layout handling
- PaddleOCR extraction
- low-confidence / suspicious-word review
- spellcheck assistance
- PaddleVL post-check
- cleanup

This folder is the multi-document extension of `1-stress-test`, but limited to one Paddle workflow versus one ABBYY workflow across many pages.

## What Was Compared

The dataset contains `7` document groups and `217` matched page pairs.

Compared document groups:

- `aeu.00037_19470820`
- `oocihm.22250`
- `oocihm.N_00126_19130805`
- `oocihm.N_00138_18940629`
- `oocihm.N_00155_18750610`
- `oocihm.N_00155_18880712`
- `oocihm.N_00219_18600707`

## Output Files

Generated outputs are stored under `test-results`.

- Overall summary workbook: `test-results/multi_document_paddle_vs_abbyy_errors_artifacts.xlsx`
- Page-level workbooks: `test-results/page-level-excels/<document>/<page>.xlsx`
- Plot dashboard: `test-results/plots/multi_document_ocr_dashboard.html`
- Plot PNG exports: `test-results/plots/png/*.png`

Each page-level workbook uses the same wide page-by-page artifact layout as the stress-test comparison script.
The plots compare Paddle against ABBYY only; there is no human-transcribed reference set for this folder yet.

## Headline Findings

Across all `217` page pairs:

- Paddle nonblank line count: `66,567`
- ABBYY nonblank line count: `49,775`
- Paddle word count: `334,312`
- ABBYY word count: `301,984`
- Paddle artifact entries: `8,779`
- ABBYY artifact entries: `6,826`

Raw size ratios vs ABBYY:

- Paddle nonblank lines vs ABBYY: `133.7%` overall
- Paddle words vs ABBYY: `110.7%` overall

Page-level artifact split:

- Paddle lower on `75` pages
- ABBYY lower on `114` pages
- Tied on `28` pages

At the highest level, the current workbook no longer shows a near-tie. `3x2` is clearly larger than ABBYY on raw output size and also clearly higher on tagged artifact rows:

- Paddle emits `32,328` more words than ABBYY
- Paddle emits `16,792` more nonblank lines than ABBYY
- Paddle produces `1,953` more artifact entries than ABBYY

That size difference matters. `3x2` is usually producing much more OCR text than ABBYY, especially at the word level. Sometimes that means better recovery. Sometimes it means extra separators, ad fragments, or short layout leftovers that survive cleanup.

The biggest pattern differences:

- Paddle produces far more `isolated marker/separator` entries: `6,417` vs `3,200`
- Paddle produces all detected `Possible duplicate lines` entries: `108` vs `0`
- ABBYY produces more `punctuation artifact` entries: `2,401` vs `520`
- ABBYY produces more `line-start artifact` entries: `429` vs `14`
- ABBYY produces slightly more `suspicious glyph` entries: `804` vs `729`
- `OCR token/phrase mismatch` and `suspicious token` counts are closer, with Paddle somewhat higher

This means the two systems fail differently:

- Paddle is more likely to leave behind separators, tile/merge leftovers, and some duplication noise
- ABBYY is more likely to produce punctuation debris, malformed line starts, BOM/control-character flags, and somewhat more suspicious glyphs
- On the current workbook, the overall artifact burden still leans toward ABBYY as the cleaner side

## Key Charts

These are the charts that best support the interpretation in this README. The full dashboard is still available at `test-results/plots/multi_document_ocr_dashboard.html`.

### 1. Word Recovery

This is the clearest coverage chart. It shows that Paddle usually emits more text than ABBYY, which is a strength on prose pages but can also inflate low-value fragments on dense layouts.

![Document Word Recovery](test-results/plots/png/document_word_recovery.png)

### 2. Total Artifacts By Document

This is the cleanest high-level comparison of which documents lean toward Paddle or ABBYY after cleanup.

![Document Artifact Totals](test-results/plots/png/document_artifact_totals.png)

### 3. Artifact Mix vs ABBYY

This chart explains why the totals alone are not enough. Paddle and ABBYY are not failing in the same way, and this is where the separator-vs-glyph split becomes obvious.

![Artifact Categories vs ABBYY](test-results/plots/png/document_artifact_categories.png)

### 4. Biggest Page-Level Swings

This is the best chart for identifying representative outlier pages.
Red bars mean Paddle had more tagged artifacts on that page, gray bars mean ABBYY had more, and the dashed center line is zero difference.

![Largest Page-Level Artifact Deltas](test-results/plots/png/page_artifact_delta.png)

## Document-Level Findings

Some broad document-level patterns from the aggregate workbook:

- `aeu.00037_19470820` is still one of the noisiest documents in the set, but the current workbook leans toward ABBYY rather than a tie. ABBYY has the lower artifact count on `5` of the `8` pages, and the document totals are `2,315` artifact entries for Paddle versus `2,121` for ABBYY, even though Paddle emits `5,411` more words.
- `oocihm.22250` is the biggest volume test in the set and stays mixed at page level, but still leans toward ABBYY overall. ABBYY has the lower artifact count on `84` pages, Paddle is lower on `65`, and `28` pages are tied. The document totals are `1,969` artifact entries for Paddle versus `1,767` for ABBYY, while Paddle emits `15,715` more words.
- `oocihm.N_00219_18600707` remains one of the strongest ABBYY wins. ABBYY has the lower artifact count on all `4` pages, and the document totals are `1,332` artifact entries for Paddle versus `744` for ABBYY. Paddle still emits `1,981` more words here, which suggests the extra output is not buying a cleaner page.
- `oocihm.N_00155_18880712` is still the best current `3x2` case. Total artifact entries are slightly lower for Paddle (`417` versus `428`), the page split is even at `4` to `4`, and Paddle emits `4,563` more words than ABBYY.
- `oocihm.N_00126_19130805` now leans toward ABBYY rather than Paddle. ABBYY has the lower artifact count on `6` of the `8` pages, and the document totals are `767` artifact entries for Paddle versus `660` for ABBYY, even though Paddle emits `1,826` more words.
- `oocihm.N_00138_18940629` is a clear ABBYY artifact win in the current workbook. ABBYY has the lower artifact count on `7` of the `8` pages, and the document totals are `1,280` artifact entries for Paddle versus `750` for ABBYY, despite near word-count parity.
- `oocihm.N_00155_18750610` is also a clear ABBYY win. ABBYY has the lower artifact count on all `4` pages, and the document totals are `699` artifact entries for Paddle versus `356` for ABBYY, even though Paddle emits `2,786` more words.

### Document Matrix: ABBYY Vs 3x2

### Paddle More Words And Less Artifacts

- `oocihm.N_00155_18880712`: `3x2` has `53,790` words versus `49,227` for ABBYY, a gain of `4,563` words. Artifact totals also favor `3x2`: `417` artifact entries versus `428` for ABBYY.

![Representative more-words less-artifacts page from oocihm.N_00155_18880712](test-data/abbyy/oocihm.N_00155_18880712/oocihm.N_00155_18880712.6.jpg)

### Paddle More Words And More Artifacts

- `aeu.00037_19470820`: `3x2` has `37,460` words versus `32,049` for ABBYY, a gain of `5,411` words. Artifact totals cut the other way: `2,315` artifact entries for `3x2` versus `2,121` for ABBYY.

![Representative more-words more-artifacts page from aeu.00037_19470820](test-data/abbyy/aeu.00037_19470820/aeu.00037_19470820.1.jpg)

- `oocihm.22250`: `3x2` has `91,399` words versus `75,684` for ABBYY, a gain of `15,715` words. Artifact totals cut the other way: `1,969` artifact entries for `3x2` versus `1,767` for ABBYY.

![Representative more-words more-artifacts page from oocihm.22250](test-data/abbyy/oocihm.22250/0160.jpg)

- `oocihm.N_00126_19130805`: `3x2` has `28,355` words versus `26,529` for ABBYY, a gain of `1,826` words. Artifact totals cut the other way: `767` artifact entries for `3x2` versus `660` for ABBYY.

![Representative more-words more-artifacts page from oocihm.N_00126_19130805](test-data/abbyy/oocihm.N_00126_19130805/oocihm.N_00126_19130805.1.jpg)

- `oocihm.N_00138_18940629`: `3x2` has `39,669` words versus `39,623` for ABBYY, a gain of `46` words. Artifact totals cut the other way: `1,280` artifact entries for `3x2` versus `750` for ABBYY.

![Representative more-words more-artifacts page from oocihm.N_00138_18940629](test-data/abbyy/oocihm.N_00138_18940629/oocihm.N_00138_18940629.1.jpg)

- `oocihm.N_00155_18750610`: `3x2` has `62,179` words versus `59,393` for ABBYY, a gain of `2,786` words. Artifact totals cut the other way: `699` artifact entries for `3x2` versus `356` for ABBYY.

![Representative more-words more-artifacts page from oocihm.N_00155_18750610](test-data/abbyy/oocihm.N_00155_18750610/oocihm.N_00155_18750610.4.jpg)

- `oocihm.N_00219_18600707`: `3x2` has `21,460` words versus `19,479` for ABBYY, a gain of `1,981` words. Artifact totals also lean toward ABBYY: `1,332` artifact entries for `3x2` versus `744` for ABBYY.

![Representative more-words more-artifacts page from oocihm.N_00219_18600707](test-data/abbyy/oocihm.N_00219_18600707/oocihm.N_00219_18600707.3.jpg)

### Paddle Less Words And Less Artifacts

There are no document-level examples in this dataset.

### Paddle Less Words And More Artifacts

There are no document-level examples in this dataset.

## Regenerating The Results

Run:

```powershell
python tools\compare_multi_document_ocr_errors.py
```

Default outputs:

- `test-results/multi_document_paddle_vs_abbyy_errors_artifacts.xlsx`
- `test-results/page-level-excels/`

To regenerate the plots, run:

```powershell
python tools\generate_multi_document_ocr_plots.py
```

Plot outputs:

- `test-results/plots/multi_document_ocr_dashboard.html`
- `test-results/plots/png/`
