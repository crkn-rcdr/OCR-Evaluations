# Multi-Document ABBYY vs Tiled 3x1 + Docparse PaddleOCR + PaddleVL Comparison

This folder contains a multi-document OCR comparison between:

- `ABBYY` outputs under `test-data/abbyy`
- `Paddle` outputs under `test-data/preprocessing-tiling_3x1_dp+paddleocr+vl+clean`

The Paddle side is the same general workflow used in the stress test:

- preprocessing
- intended `3x1` tiling with docparse layout handling
- PaddleOCR extraction
- low-confidence / suspicious-word review
- spellcheck assistance
- PaddleVL post-check
- cleanup

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

- Paddle line count: `58,580`
- ABBYY line count: `66,166`
- Paddle word count: `308,804`
- ABBYY word count: `302,004`
- Paddle artifact entries: `10,614`
- ABBYY artifact entries: `11,056`

Coverage ratios from the plots:

- Paddle line recovery vs ABBYY: `88.5%` overall
- Paddle word recovery vs ABBYY: `102.3%` overall

Page-level split:

- Paddle lower on `111` pages
- ABBYY lower on `91` pages
- Tied on `15` pages

This is the real `3x1` result, and it is meaningfully different from the earlier duplicated `3x2` placeholder. Paddle now has both the lower total artifact count and the page-win edge, but the margin is coming from a very specific tradeoff:

- Paddle recovers `6,800` more words than ABBYY
- Paddle emits `7,586` fewer lines than ABBYY
- Paddle still carries the much larger separator burden
- ABBYY still carries the much larger glyph and punctuation burden

So this `3x1` run no longer looks like a simple over-extraction pass. It looks more like a tighter extraction pass that often keeps usable text while collapsing some line structure and still over-preserving separators on hard layouts.

The biggest pattern differences in `3x1` are still structural rather than cosmetic:

- Paddle produces far more `isolated marker/separator` entries: `5,922` vs `2,962`
- Paddle produces all detected `duplicate/tile overlap` entries: `102` vs `0`
- ABBYY produces far more `suspicious glyph` entries: `6,017` vs `3,063`
- ABBYY produces far more `punctuation artifact` entries: `2,386` vs `465`
- ABBYY produces more `line-start artifact` entries: `298` vs `9`
- `OCR token/phrase mismatch` and `suspicious token` counts are closer, with Paddle somewhat higher

So the `3x1` workflow is not simply cleaner or dirtier. It fails differently:

- Paddle is more likely to over-preserve separators, short layout fragments, and some duplication noise
- ABBYY is more likely to collapse into glyph debris, punctuation debris, and malformed line starts
- Paddle's aggregate edge comes mostly from avoiding ABBYY's character-level breakdown often enough to offset its own separator-heavy failures

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


## 3x2 vs 3x1

The `3x1` run looks better than the `3x2` run on the artifact metric used in this dataset.

Side-by-side, the main aggregate differences are:

- `3x2` Paddle artifact entries: `10,999`
- `3x1` Paddle artifact entries: `10,614`
- `3x2` page wins vs ABBYY: Paddle `97`, ABBYY `107`, ties `13`
- `3x1` page wins vs ABBYY: Paddle `111`, ABBYY `91`, ties `15`
- `3x2` line recovery vs ABBYY: `100.6%`
- `3x1` line recovery vs ABBYY: `88.5%`
- `3x2` word recovery vs ABBYY: `110.7%`
- `3x1` word recovery vs ABBYY: `102.3%`

The high-level artifact and recovery picture still points the same way as the ABBYY comparison workbook: `3x1` is the better-balanced workflow, while `3x2` is the more expansive one.

![Document Artifact Totals](test-results/plots/png/document_artifact_totals.png)

That means the `3x2` workflow is the more aggressive extractor, while `3x1` is the tighter one:

- `3x2` emits about `25,511` more words than ABBYY
- `3x1` emits about `6,800` more words than ABBYY
- `3x2` stays near ABBYY on line count
- `3x1` emits far fewer lines than ABBYY

The artifact mix also moved in the right direction with `3x1`:

- `isolated marker/separator`: `6,034` in `3x2` down to `5,922` in `3x1`
- `suspicious glyph`: `3,316` down to `3,063`
- `punctuation artifact`: `520` down to `465`
- `line-start artifact`: `15` down to `9`
- `abbreviation/spacing`: `261` down to `241`

Not every category improved:

- `OCR token/phrase mismatch`: `345` in `3x2` up to `385` in `3x1`
- `suspicious token`: `1,077` up to `1,086`

But those increases are smaller than the gains in the categories that most often made the `3x2` run look over-extracted.

The biggest practical shift is in `oocihm.22250`, where `3x2` lost to ABBYY by page count (`70` Paddle wins vs `94` ABBYY wins) but `3x1` flips that to a narrow Paddle edge (`83` vs `79`, with `15` ties). `oocihm.N_00155_18750610` also improves from a `3` to `1` page split in `3x2` to a clean `4` to `0` Paddle sweep in `3x1`. The main hard case does not change: `oocihm.N_00219_18600707` is still an ABBYY sweep in both tiling variants.

There is now also a direct ABBYY word-coverage workbook in this folder:

- workbook: `test-results/tiling_3x2_vs_3x1_abbyy_word_coverage.xlsx`
- dashboard: `test-results/plots/tiling_3x2_vs_3x1_abbyy_word_coverage_dashboard.html`

That workbook asks a different question than the artifact analysis: how much of ABBYY's page vocabulary each tiling run actually captures, and how far above or below ABBYY each run lands on raw page size.

The coverage result is narrow but consistent in favor of `3x2`:

- overall ABBYY token-occurrence coverage: `3x2 = 93.80%`, `3x1 = 92.98%`
- overall ABBYY unique-token coverage: `3x2 = 90.61%`, `3x1 = 90.19%`
- pages with better ABBYY token coverage: `3x2 = 156`, `3x1 = 14`, ties `24`

![ABBYY Token Coverage by Document](test-results/plots/png/tiling_3x2_vs_3x1_abbyy_word_coverage.png)

But the precision result cuts the other way and explains why `3x1` can still look cleaner overall on the artifact metric, even though `3x2` captures more words:

- token precision vs ABBYY: `3x2 = 84.45%`, `3x1 = 90.56%`
- pages closest to ABBYY word count: `3x2 = 24`, `3x1 = 165`, ties `7`

So `3x2` captures slightly more of ABBYY's tokens, while `3x1` stays much closer to ABBYY's page size. If your priority is maximum word capture, that still favors `3x2`.

![Token Precision vs ABBYY by Document](test-results/plots/png/tiling_3x2_vs_3x1_abbyy_word_precision.png)

There is now also a direct `3x2` vs `3x1` line-diff analysis in this folder:

- workbook: `test-results/tiling_3x2_vs_3x1_extra_lines.xlsx`
- dashboard: `test-results/plots/tiling_3x2_vs_3x1_extra_lines_dashboard.html`

That comparison does not use ABBYY at all. It simply asks which lines are unique to one tiling run versus the other on the same page.

The headline result is decisive:

- shared matched nonblank lines: `39,507`
- `3x2`-only lines: `27,060`
- `3x1`-only lines: `19,073`
- pages where `3x2` has more unique-only lines: `200`
- pages where `3x1` has more unique-only lines: `11`
- tied pages: `6`

So `3x2` is not just slightly more expansive than `3x1`. It is substantially more expansive on almost the entire dataset.

![Document Extra-Line Totals](test-results/plots/png/tiling_3x2_vs_3x1_document_extra_lines.png)

The type mix matters too:

- `3x2`-only separator/symbol lines: `371`
- `3x1`-only separator/symbol lines: `398`
- `3x2`-only short fragments: `4,949`
- `3x1`-only short fragments: `3,652`
- `3x2`-only text lines: `21,740`
- `3x1`-only text lines: `15,023`

That means the `3x2` expansion is not just extra separator junk. It is adding many more full text lines as well. But without human ground truth, those extra text lines still cannot be assumed to be correct text recovery rather than duplicated, over-split, or layout-driven spillover.

![Extra-Line Type Mix](test-results/plots/png/tiling_3x2_vs_3x1_extra_line_types.png)

At the document level, the biggest extra-line gap is in `oocihm.22250`, where `3x2` has `11,994` unique-only lines and `3x1` has `6,557`. `oocihm.N_00155_18750610` is another strong example: `3,485` vs `2,564`. The largest page-level surges are all `3x2` pages from `oocihm.N_00155_18750610`, especially pages `.1` through `.4`.

![Largest Page-Level Extra-Line Deltas](test-results/plots/png/tiling_3x2_vs_3x1_page_extra_line_delta.png)

## Document-Level Findings

Some broad document-level patterns from the aggregate workbook and refreshed plots:

- `aeu.00037_19470820` is still the noisiest document on both sides and remains close overall. Paddle has the lower artifact count on `4` of the `8` pages, and ABBYY has the lower artifact count on the other `4`. The document-wide totals are `4,022` artifact entries for Paddle versus `4,107` artifact entries for ABBYY. It is still the best example of the separator-vs-punctuation tradeoff.
- `oocihm.22250` is the biggest volume test in the set and stays genuinely mixed. Paddle has the lower artifact count on `83` pages, ABBYY has the lower artifact count on `79`, and `15` pages are tied. Even so, the document-wide totals still lean slightly toward ABBYY: `2,040` artifact entries for Paddle versus `1,943` artifact entries for ABBYY. Coverage is below ABBYY here at `81.0%` of ABBYY line count and `96.8%` of ABBYY word count, which suggests `3x1` is often suppressing short fragments but not clearly beating ABBYY on this whole volume.
- `oocihm.N_00219_18600707` is still the strongest document-level ABBYY win by summed artifact entries. ABBYY has the lower artifact count on all `4` pages, and the document-wide totals are `1,266` artifact entries for Paddle versus `939` artifact entries for ABBYY. Paddle word recovery is still above ABBYY (`107.2%` of ABBYY word count) even though Paddle line recovery is below (`94.2%` of ABBYY line count), which points to extra fragment extraction on the hardest ad-heavy pages.
- `oocihm.N_00155_18880712` remains the strongest Paddle win. Paddle has the lower artifact count on all `8` pages, and the document-wide totals are `443` artifact entries for Paddle versus `863` artifact entries for ABBYY. This is the clearest prose-led case where ABBYY's glyph and punctuation corruption outweigh Paddle's separator noise.
- `oocihm.N_00126_19130805` is one of the strongest clean Paddle wins. Paddle has the lower artifact count on `7` of the `8` pages, while ABBYY is lower on `1`. The document-wide totals are `731` artifact entries for Paddle versus `897` artifact entries for ABBYY. Paddle reaches only `76.4%` of ABBYY line count here but still slightly exceeds ABBYY on words (`100.6%` of ABBYY word count), which suggests fewer short stray lines rather than obvious text loss.
- `oocihm.N_00138_18940629` remains the best mixed-layout stress case in the set. Paddle has the lower artifact count on `5` of the `8` pages, and ABBYY is lower on `3`. The document-wide totals are nearly even: `1,354` artifact entries for Paddle versus `1,386` artifact entries for ABBYY. It still contains both the biggest single-page Paddle win and one of the biggest ABBYY wins.
- `oocihm.N_00155_18750610` is now a clean Paddle sweep by page count. Paddle has the lower artifact count on all `4` pages, and the document-wide totals are `758` artifact entries for Paddle versus `921` artifact entries for ABBYY. That is a strong result because it is driven by dense article pages, not just the easiest prose pages.

### Document Matrix

#### Paddle More Words And Less Artifacts

- `oocihm.N_00155_18880712`: `3x1` has `53,735` words versus `49,224` for ABBYY, a gain of `4,511` words. Artifact totals also favor `3x1`: `443` artifact entries versus `863` for ABBYY.

![Representative more-words less-artifacts page from oocihm.N_00155_18880712](test-data/abbyy/oocihm.N_00155_18880712/oocihm.N_00155_18880712.6.jpg)

- `aeu.00037_19470820`: `3x1` has `35,459` words versus `32,046` for ABBYY, a gain of `3,413` words. Artifact totals also favor `3x1`: `4,022` artifact entries versus `4,107` for ABBYY.

![Representative more-words less-artifacts page from aeu.00037_19470820](test-data/abbyy/aeu.00037_19470820/aeu.00037_19470820.1.jpg)

- `oocihm.N_00126_19130805`: `3x1` has `26,681` words versus `26,523` for ABBYY, a gain of `158` words. Artifact totals also favor `3x1`: `731` artifact entries versus `897` for ABBYY.

![Representative more-words less-artifacts page from oocihm.N_00126_19130805](test-data/abbyy/oocihm.N_00126_19130805/oocihm.N_00126_19130805.1.jpg)

#### Paddle More Words And More Artifacts

- `oocihm.N_00219_18600707`: `3x1` has `20,878` words versus `19,477` for ABBYY, a gain of `1,401` words. Artifact totals cut the other way: `1,266` artifact entries for `3x1` versus `939` for ABBYY.

![Representative more-words more-artifacts page from oocihm.N_00219_18600707](test-data/abbyy/oocihm.N_00219_18600707/oocihm.N_00219_18600707.3.jpg)

#### Paddle Less Words And Less Artifacts

- `oocihm.N_00155_18750610`: `3x1` has `59,063` words versus `59,391` for ABBYY, a loss of `328` words. Artifact totals still favor `3x1`: `758` artifact entries versus `921` for ABBYY.

![Representative less-words less-artifacts page from oocihm.N_00155_18750610](test-data/abbyy/oocihm.N_00155_18750610/oocihm.N_00155_18750610.4.jpg)

#### Paddle Less Words And More Artifacts

- `oocihm.22250`: `3x1` has `73,254` words versus `75,671` for ABBYY, a loss of `2,417` words. Artifact totals also lean toward ABBYY: `2,040` artifact entries for `3x1` versus `1,943` for ABBYY.

![Representative less-words more-artifacts page from oocihm.22250](test-data/abbyy/oocihm.22250/0160.jpg)

Cross-run recommendation is consolidated in [4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl/README.md](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\README.md). This section keeps the `3x1` vs ABBYY analysis and the direct `3x2` vs `3x1` comparison data, but the final workflow recommendation now lives in the no-tiling README so the dataset-series guidance stays in one place.

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
