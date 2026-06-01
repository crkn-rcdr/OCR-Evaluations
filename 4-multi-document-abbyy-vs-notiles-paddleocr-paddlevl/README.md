# Multi-Document ABBYY vs No-Tiling PaddleOCR + PaddleVL Comparison

This folder contains a multi-document OCR comparison between:

- `ABBYY` outputs under `test-data/abbyy`
- `Paddle` outputs under `test-data/preprocess-notiles-paddleocr-paddlevl`

The Paddle side uses the same general preprocessing and post-OCR review stack as the tiled runs, but without any page tiling:

- preprocessing
- PaddleOCR extraction
- low-confidence / suspicious-word review
- spellcheck assistance
- PaddleVL post-check
- cleanup

This README covers two related questions:

1. how the no-tiling run compares with ABBYY on the same `217` pages
2. how the no-tiling run compares with the tiled `3x1` and `3x2` variants already analyzed elsewhere in this dataset series

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

Main no-tiling vs ABBYY outputs:

- overall workbook: [multi_document_paddle_vs_abbyy_errors_artifacts.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\multi_document_paddle_vs_abbyy_errors_artifacts.xlsx)
- page-level workbooks: [page-level-excels](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\page-level-excels)
- dashboard: [multi_document_ocr_dashboard.html](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\plots\multi_document_ocr_dashboard.html)

Cross-run outputs created in this folder:

- three-way ABBYY token coverage workbook: [paddle_variants_abbyy_word_coverage.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\paddle_variants_abbyy_word_coverage.xlsx)
- three-way artifact workbook: [paddle_variants_abbyy_artifacts.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\paddle_variants_abbyy_artifacts.xlsx)
- no-tiling vs `3x1` extra-line workbook: [notiling_vs_3x1_extra_lines.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\notiling_vs_3x1_extra_lines.xlsx)
- `3x2` vs no-tiling extra-line workbook: [3x2_vs_notiling_extra_lines.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\3x2_vs_notiling_extra_lines.xlsx)

Cross-run dashboards:

- [paddle_variants_abbyy_word_coverage_dashboard.html](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\plots\paddle_variants_abbyy_word_coverage_dashboard.html)
- [paddle_variants_abbyy_artifacts_dashboard.html](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\plots\paddle_variants_abbyy_artifacts_dashboard.html)
- [notiling_vs_3x1_extra_lines_dashboard.html](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\plots\notiling_vs_3x1_extra_lines_dashboard.html)
- [3x2_vs_notiling_extra_lines_dashboard.html](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\plots\3x2_vs_notiling_extra_lines_dashboard.html)

## Headline Findings

Across all `217` no-tiling vs ABBYY page pairs:

- no-tiling Paddle nonblank line count: `55,721`
- ABBYY nonblank line count: `49,775`
- no-tiling Paddle word count: `299,604`
- ABBYY word count: `301,984`
- no-tiling Paddle artifact entries: `7,874`
- ABBYY artifact entries: `11,041`

Page-level split:

- no tiling lower on `94` pages
- ABBYY lower on `109` pages
- tied on `14` pages

So the no-tiling run is not winning more pages than ABBYY, but it is dramatically lower on total artifact entries overall. The reason is that when no tiling is better, it is often better by a very large margin.

That is the main surprise in this dataset:

- no tiling is the cleanest Paddle variant by aggregate artifact count
- but it is not the best balanced variant once coverage is considered

Its failure pattern is still recognizably Paddle-like:

- `isolated marker/separator`: `4,055` vs ABBYY `2,962`
- `suspicious token`: `1,132` vs ABBYY `890`
- `OCR token/phrase mismatch`: `283` vs ABBYY `124`

But no tiling is much lighter than the tiled runs on exactly the categories that made them look noisy:

- `Possible duplicate lines`: `32`
- `punctuation artifact`: `126`
- `suspicious glyph`: `2,652`

ABBYY still carries far more glyph, punctuation, and malformed-line-start debris:

- `suspicious glyph`: `6,017`
- `punctuation artifact`: `2,386`
- `line-start artifact`: `298`

## Key Charts

These are the charts that best support the interpretation in this README.

### 1. No-Tiling Word Recovery vs ABBYY

This shows the raw coverage problem directly. No tiling is often cleaner, but it does not hold line structure as well as ABBYY.

![Document Word Recovery](test-results/plots/png/document_word_recovery.png)

### 2. No-Tiling Artifact Totals vs ABBYY

This is the clearest statement of why the no-tiling run looks attractive at first glance: the total artifact count drops sharply on most documents.

![Document Artifact Totals](test-results/plots/png/document_artifact_totals.png)

### 3. Error-Type Mix vs ABBYY

This chart explains where that artifact improvement comes from. No tiling suppresses a lot of the noise that the tiled runs introduced, but it is still separator-heavy.

![Artifact Categories vs ABBYY](test-results/plots/png/document_artifact_categories.png)

### 4. Biggest Page-Level Swings

These outliers explain most of the aggregate gap. Red bars mean Paddle had more tagged artifacts; gray bars mean ABBYY had more.

![Largest Page-Level Artifact Deltas](test-results/plots/png/page_artifact_delta.png)


## Document-Level Findings

The no-tiling run is extremely polarized by document:

- `aeu.00037_19470820`: no-tiling Paddle has the lower artifact count than ABBYY on all `8` pages, while ABBYY is lower on `0`. The document-level artifact totals are `2,668` for no-tiling Paddle versus `4,114` for ABBYY. This is the clearest evidence that removing tiling can sharply reduce the punctuation-and-glyph collapse on dense results pages.
- `oocihm.N_00126_19130805`: no-tiling Paddle is lower than ABBYY on all `8` pages, while ABBYY is lower on `0`. The document-level artifact totals are `551` for no-tiling Paddle versus `898` for ABBYY.
- `oocihm.N_00155_18750610`: no-tiling Paddle is lower than ABBYY on all `4` pages, while ABBYY is lower on `0`. The document-level artifact totals are `198` for no-tiling Paddle versus `920` for ABBYY.
- `oocihm.N_00155_18880712`: no-tiling Paddle is lower than ABBYY on all `8` pages, while ABBYY is lower on `0`. The document-level artifact totals are `263` for no-tiling Paddle versus `863` for ABBYY.
- `oocihm.N_00138_18940629`: no-tiling Paddle is lower than ABBYY on `7` pages, and ABBYY is lower on `1`. The document-level artifact totals are `807` for no-tiling Paddle versus `1,384` for ABBYY.
- `oocihm.N_00219_18600707`: this one is genuinely mixed. No-tiling Paddle has the lower artifact count on `2` of the `4` pages, and ABBYY has the lower artifact count on the other `2` pages. Across the whole document, the summed artifact-entry totals still lean slightly toward no tiling: `814` artifact entries for no-tiling Paddle versus `936` artifact entries for ABBYY.
- `oocihm.22250`: this is the hardest counterexample. ABBYY is lower on `106` pages, no-tiling Paddle is lower on only `57`, and `14` pages tie. The document-level artifact totals also lean toward ABBYY: `2,573` for no-tiling Paddle versus `1,926` for ABBYY. So this volume is the clearest case where the no-tiling cleanup gains are not enough to outweigh the pages where ABBYY stays structurally safer.

So the no-tiling run is not simply “better on clean prose and worse on hard layouts.” It can also beat ABBYY on some very dense structure-heavy pages. The real pattern is narrower:

- no tiling sharply suppresses some of the duplicated or fragmented text behavior that tiling introduced
- but it also gives up too much consistent coverage across the full corpus

## No Tiling vs 3x1 vs 3x2

The cross-run comparison changes the recommendation.

By aggregate artifact count, the ordering is clear:

- no tiling: `7,874`
- `3x1`: `10,614`
- `3x2`: `10,999`

![Paddle Variant Artifact Totals](test-results/plots/png/paddle_variants_artifact_totals.png)

Raw document word counts tell the complementary story: `3x2` is the highest-volume run on most documents, but no tiling is actually the top word-count run on `oocihm.22250` and `oocihm.N_00219_18600707`. ABBYY and `3x1` sit in the middle depending on the document.

![Paddle Variant Word Counts vs ABBYY](test-results/plots/png/paddle_variants_abbyy_word_counts.png)

But once ABBYY token coverage is used as the recall check, no tiling drops behind both tiled variants:

- `3x2` ABBYY token coverage: `93.80%`
- `3x1` ABBYY token coverage: `92.98%`
- no tiling ABBYY token coverage: `79.37%`

![ABBYY Token Coverage by Document](test-results/plots/png/paddle_variants_abbyy_word_coverage.png)

The precision picture is different again:

- `3x1` precision vs ABBYY: `90.56%`
- `3x2` precision vs ABBYY: `84.45%`
- no tiling precision vs ABBYY: `80.03%`

![Token Precision vs ABBYY by Document](test-results/plots/png/paddle_variants_abbyy_word_precision.png)

That is why the no-tiling run does not replace `3x1` as the default recommendation. It is cleaner, but it gives up too much word coverage on some documents even though it does well on others, and it is not the strongest variant on the token-coverage metric.

The direct line-diff workbooks show the same thing from another angle:

- no-tiling-only lines vs `3x1`: `21,788`
- `3x1`-only lines vs no tiling: `24,647`
- no-tiling-only lines vs `3x2`: `26,832`
- `3x2`-only lines vs no tiling: `37,678`

![No Tiling vs 3x1 Document Extra Lines](test-results/plots/png/no_tiling_vs_3x1_document_extra_lines.png)

![3x2 vs No Tiling Document Extra Lines](test-results/plots/png/3x2_vs_no_tiling_document_extra_lines.png)

So no tiling is not just “`3x1` minus tile overlap.” It is a materially different OCR pass, with lower word capture on some documents and higher word capture on others.

One important note about the merged artifact workbook:

- [paddle_variants_abbyy_artifacts.xlsx](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\test-results\paddle_variants_abbyy_artifacts.xlsx) uses the no-tiling ABBYY pairing as the canonical ABBYY artifact baseline
- that is intentional because the `ABBYY` mismatch-tag counts are pair-dependent, while the Paddle totals are the quantities being compared side by side


## Document Matrix

### Paddle More Words And Less Artifacts

- `oocihm.N_00219_18600707`: no tiling has `25,831` words versus `19,479` for ABBYY, a gain of `6,352` words. Artifact totals also favor no tiling: `814` artifact entries versus `936` for ABBYY.

![Representative more-words less-artifacts page from oocihm.N_00219_18600707](test-data/abbyy/oocihm.N_00219_18600707/oocihm.N_00219_18600707.3.jpg)

- `oocihm.N_00155_18880712`: no tiling has `50,200` words versus `49,227` for ABBYY, a gain of `973` words. Artifact totals also favor no tiling: `263` artifact entries versus `863` for ABBYY.

![Representative more-words less-artifacts page from oocihm.N_00155_18880712](test-data/abbyy/oocihm.N_00155_18880712/oocihm.N_00155_18880712.6.jpg)

### Paddle More Words And More Artifacts

- `oocihm.22250`: no tiling has `102,132` words versus `75,684` for ABBYY, a gain of `26,448` words. Artifact totals cut the other way: `2,573` artifact entries for no tiling versus `1,926` for ABBYY.

![Representative more-words more-artifacts page from oocihm.22250](test-data/abbyy/oocihm.22250/0160.jpg)

### Paddle Less Words And Less Artifacts

- `oocihm.N_00155_18750610`: no tiling has `27,204` words versus `59,393` for ABBYY, a loss of `32,189` words. Artifact totals still favor no tiling strongly: `198` artifact entries versus `920` for ABBYY.

![Representative less-words less-artifacts page from oocihm.N_00155_18750610](test-data/abbyy/oocihm.N_00155_18750610/oocihm.N_00155_18750610.4.jpg)

- `oocihm.N_00138_18940629`: no tiling has `36,461` words versus `39,623` for ABBYY, a loss of `3,162` words. Artifact totals still favor no tiling: `807` artifact entries versus `1,384` for ABBYY.

![Representative less-words less-artifacts page from oocihm.N_00138_18940629](test-data/abbyy/oocihm.N_00138_18940629/oocihm.N_00138_18940629.7.jpg)

- `oocihm.N_00126_19130805`: no tiling has `26,438` words versus `26,529` for ABBYY, a loss of only `91` words. Artifact totals also favor no tiling: `551` artifact entries versus `898` for ABBYY.

![Representative less-words less-artifacts page from oocihm.N_00126_19130805](test-data/abbyy/oocihm.N_00126_19130805/oocihm.N_00126_19130805.1.jpg)

### Paddle Less Words And More Artifacts

There are no document-level examples in this dataset. Every document either:

- gains words with more artifacts,
- gains words with fewer artifacts, or
- loses words while still reducing artifacts.

## Recommendation

This is the canonical recommendation for the three Paddle variants in this dataset series.

These rankings use ABBYY as the baseline reference at `301,984` raw words.

If the deciding metric is `raw total word count`, the ranking is:

1. `3x2 + docparse + PaddleOCR + PaddleVL`
   Measured as `334,312` raw words.
2. `3x1 + docparse + PaddleOCR + PaddleVL`
   Measured as `308,801` raw words.
3. no tiling
   Measured as `299,604` raw words.

If the deciding metric is `best overall balance of raw word volume and artifact control`, the ranking is:

1. `3x1 + docparse + PaddleOCR + PaddleVL`
   Measured as `308,801` raw words with `10,614` artifact entries.
2. `3x2 + docparse + PaddleOCR + PaddleVL`
   Measured as `334,312` raw words with `10,999` artifact entries.
3. no tiling
   Measured as `299,604` raw words with `7,874` artifact entries.
   Canonical artifact baseline in the merged workbook: `11,041` artifact entries.

If the deciding metric is `lowest artifact count`, the ranking is:

Using ABBYY as the merged-workbook baseline at `11,041` artifact entries:

1. no tiling
   Measured as `7,874` artifact entries.
2. `3x1 + docparse + PaddleOCR + PaddleVL`
   Measured as `10,614` artifact entries.
3. `3x2 + docparse + PaddleOCR + PaddleVL`
   Measured as `10,999` artifact entries.

So the no-tiling run is not a failure. It is a real and useful point on the tradeoff curve:

- much cleaner than the tiled runs
- often dramatically cleaner than ABBYY on the right pages
- strongest on raw cleanliness, but not the strongest overall word-capture option across the full dataset


## Regenerating The Results

No-tiling vs ABBYY:

```powershell
python tools\compare_multi_document_ocr_errors.py
python tools\generate_multi_document_ocr_plots.py
```

Three-way comparison outputs:

```powershell
python tools\compare_paddle_variants_word_coverage_vs_abbyy.py
python tools\generate_paddle_variants_word_coverage_plots.py
python tools\compare_paddle_variants_artifacts_vs_abbyy.py
python tools\generate_paddle_variants_artifact_plots.py
```

Pairwise extra-line comparisons:

```powershell
python tools\compare_pairwise_extra_lines.py --run-a-label "no tiling" --run-a-dir test-data\preprocess-notiles-paddleocr-paddlevl --run-b-label "3x1" --run-b-dir ..\3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl\test-data\preprocessing-tiling_3x1_dp+paddleocr+vl+clean --output test-results\notiling_vs_3x1_extra_lines.xlsx
python tools\generate_pairwise_extra_line_plots.py --workbook test-results\notiling_vs_3x1_extra_lines.xlsx --output-html test-results\plots\notiling_vs_3x1_extra_lines_dashboard.html --output-png-dir test-results\plots\png
python tools\compare_pairwise_extra_lines.py --run-a-label "3x2" --run-a-dir ..\2-multi-document-abbyy-vs-tiled3x2+docparse-paddleocr-paddlevl\test-data\preprocessing-tiling_3x2_dp+paddleocr+vl+clean --run-b-label "no tiling" --run-b-dir test-data\preprocess-notiles-paddleocr-paddlevl --output test-results\3x2_vs_notiling_extra_lines.xlsx
python tools\generate_pairwise_extra_line_plots.py --workbook test-results\3x2_vs_notiling_extra_lines.xlsx --output-html test-results\plots\3x2_vs_notiling_extra_lines_dashboard.html --output-png-dir test-results\plots\png
```
