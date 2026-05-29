## Testing 

### Source image
![alt text](testdata/source/large/oocihm.N_00155_18750610.4.jpg)

#### OCR Challenges

This test image is a difficult historical newspaper page rather than a clean
modern scan. The page combines several OCR failure modes at once:

- very small text across many narrow multi-column regions
- large page dimensions that force text to be read at a tiny effective scale
- uneven background and faded paper tone
- black border / dark scanner margin around the page
- vertical scratches, dust, speckling, and film or scan artifacts
- dense layout with poems, article columns, notices, and mixed block widths
- thin separators and narrow gutters that can confuse page segmentation

This is exactly the kind of page where a simple one-pass OCR run often loses
small words, merges adjacent columns, or misreads punctuation. It is also the
kind of page where ABBYY benefits from its surrounding document-analysis stack,
so Paddle needed extra supporting steps to get closer.

### Methodologies

Comparing Paddle OCR with ABBYY on this page required more than switching OCR models. The testing in this repo is built around a Paddle OCR expirement pipeline which includes stages to: improve the page before OCR, reduce page scale problems with tiling, optionally route crops through layout-aware parsing, and then apply targeted cleanup or second-pass correction.

At a high level, the variants in `test-results/paddlecomp` represent this progression:

- baseline PP-OCR with lighter preprocessing
- PP-OCR with heavier segmentation through tiling and DocLayout
- PP-OCR followed by post-OCR VL correction using different backends

The goal was not only to increase raw character accuracy, but also to reduce:

- broken reading order
- dropped or merged words in dense columns
- punctuation artifacts
- OCR mistakes that are locally ambiguous but visually recoverable from crops

#### Pre-processing

Historical pages often benefit from mild cleanup before local OCR.
We looked at a few preprocessing steps such as:

- `light_clean` applies a very light denoising pass to remove small scanner
  grime and speckle without heavily changing the page
- `background_flatten` estimates the page's uneven gray background and evens it
  out so the text stands out more consistently across the sheet
- `contrast` / CLAHE boosts local contrast in small regions, which can make
  faint strokes and thin newspaper type easier for OCR to separate from the
  page
- `deskew` tries to detect whether the whole page is slightly rotated and, if
  so, rotates it back to a more level reading angle
- `sauvola_binary` converts the page into a black-and-white style text image
  using adaptive thresholding, which can help when foreground and background
  are hard to separate but can also throw away useful grayscale detail
- black-border cropping before OCR tries to detect the real page area inside a
  dark scanner border, crop to that region, and then keep track of the offset
  so OCR coordinates can still be mapped back to the original image

For this page, preprocessing matters because the text sits inside a large dark
border and on an uneven gray background. Even when OCR can still "see" the
letters, cleanup can materially improve text detection, reduce false positives
in the margin, and increase the legibility of small print.

After testing, the preprocessing choices that gave the best results on this
page were:

- isolate the real page from the dark outer border
- flatten the background so text stands out more consistently

Other preprocessing options were tested, but on this image they produced worse
results overall than this lighter combination.

#### Tiling

Large broadsheet pages are one of the main reasons tiling was necessary. The rationale is straightforward: when the full page is too large and the text too small, splitting the page into smaller regions gives the recognizer more effective resolution per text line.

For this repo, the important tile variants are:

- `3x1 grid`
  - a simpler fixed split for tall or column-heavy pages
- `3x2 grid`
  - a stronger fixed split for dense newspaper layouts
- `doclayout_v3`
  - feed the full source image into `PP-DocLayoutV3` first, then use the
    detected layout regions as OCR subtiles
- `3x2 grid + PP-DocLayoutV3`
  - fixed tiling first, then layout-guided sub-segmentation inside each large
    tile using DocLayout-style parsing

After testing, `3x2 grid + PP-DocLayoutV3` was the tiling strategy we kept because it
returned the largest amount of text or word content on this page. The simpler
tiling options were still useful as comparison points, but this combination
recovered more of the newspaper content overall.

#### Suspicious Word level VL Correction

The PaddleOCR expirement pipeline also adds a second-pass correction stage for `PP-OCRv5`.
Instead of rerunning the whole page through a larger model, it can:

- inspect OCR output for suspicious or low-confidence words
- crop those words or local line regions
- send the crops to a VL backend
- optionally apply accepted corrections back into the OCR text

That design is useful on pages like this because many errors are local:

- a single blurry short word
- punctuation fused into neighboring letters
- one broken token in an otherwise readable line

The current comparison folders in this repo reflect that idea with several
post-OCR VL backends:

- `large-ppocr-preproccess3x2-PP-DocLayoutV3-paddlevl`
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-olmocr`
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-chandra`
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-deepseek`

These are best understood as PP-OCR-centered workflows that then use a second
vision-language model to review difficult words after the first OCR pass.

A "suspicious" word is not just any low-confidence token. The
post-OCR code assigns each candidate a weirdness score and only sends it for VL
review when that score is high enough. The score is driven by OCR-like warning
signs such as:

- odd glyphs or unusual characters
- repeated punctuation
- repeated letters
- alphabetic words with no vowels
- OCR-confusable starts such as `rn` or `vv`
- odd internal casing
- unusual character patterns relative to the document's own vocabulary
- tokens that are suspiciously close to common document words
- spellcheck misses
- suspicious letter-digit mixtures
- merged or malformed word-box text

Low line confidence can also increase the score, but `suspicious` mode is more
targeted than the broader `low_confidence` mode. In practice, it is trying to
find words that look specifically like OCR errors, not just words that happen
to come from a weaker line.

#### Punctuation Cleaning

The PaddleOCR expirement pipeline also included a punctuation-cleaning stage. This exists
because historical newspaper OCR often produces artifacts that are not full
word-recognition failures but still hurt readability and comparison:

- stray commas or periods
- broken quotes
- repeated punctuation
- punctuation glued to adjacent text incorrectly

### Comparisons

The main comparison artifacts are:

- [test-results/paddle_vs_abbyy_errors_artifacts.xlsx](test-results/paddle_vs_abbyy_errors_artifacts.xlsx)
  - workbook comparing matching Paddle and ABBYY outputs, with one worksheet
    per matched Paddle TXT file
- [test-results/first_article_ocr_comparison.xlsx](test-results/first_article_ocr_comparison.xlsx)
  - workbook comparing a human transcription against ABBYY plus every
    `first-article.txt` found under `test-results/paddlecomp`

The current `paddlecomp` result folders are:

- `large-ppocr-preprocess`
  - baseline local PP-OCR preprocessing run
- `large-ppcor-preproccess-3x2-PP-DocLayoutV3`
  - PP-OCR with heavier segmentation through 3x2 tiling plus DocLayout-style
    parsing
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-paddlevl`
  - same broader PP-OCR pipeline with PaddleVL-based post-OCR correction
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-olmocr`
  - same broader PP-OCR pipeline with olmOCR-based post-OCR correction
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-chandra`
  - same broader PP-OCR pipeline with Chandra-based post-OCR correction
- `large-ppocr-preproccess3x2-PP-DocLayoutV3-deepseek`
  - same broader PP-OCR pipeline with DeepSeek OCR-based post-OCR correction

Taken together, these tests are trying to answer a practical question rather
than only a model-leaderboard question:

- how far can open Paddle-centered workflows be pushed toward ABBYY-quality OCR
  on a genuinely difficult newspaper page
- which extra steps matter most: preprocessing, stronger segmentation, or
  second-pass VL correction

### Results

#### Whole-page recovery vs ABBYY

The workbook
[test-results/paddle_vs_abbyy_errors_artifacts.xlsx](test-results/paddle_vs_abbyy_errors_artifacts.xlsx)
shows that the biggest jump came from tiling plus DocLayout-style parsing.

The `Preprocess only` run was far behind ABBYY in raw coverage:

- Paddle line count: `992`
- ABBYY line count: `2517`
- Paddle word count: `7174`
- ABBYY word count: `15999`

So preprocessing by itself did not recover enough of the newspaper page.
The main failure at that stage was under-extraction: too much page content was
still being missed.

The `3x2 grid + PP-DocLayoutV3 only` run changed that completely:

- Paddle line count: `2522`
- ABBYY line count: `2517`
- Paddle word count: `16685`
- ABBYY word count: `15999`

That is why `3x2 grid + PP-DocLayoutV3` was kept for all subsequent runs. It brought the page back to roughly the same scale of recoverable content as ABBYY. For the remainder of the dicussion it will be labeled as the `PaddleOCR (No VL)` run. 

![Whole-page line recovery](test-results/plots/png/line_count_recovery.png)

![Whole-page word recovery](test-results/plots/png/word_count_recovery.png)

![Whole-page word counts](test-results/plots/png/whole_page_word_counts.png)

That shift also changed the error profile. After tiling, the dominant Paddle
problems were no longer missing huge parts of the page, but rather:

- overlap or duplicate tile output
- joined-word or spacing artifacts
- suspicious tokens and line-start garbage
- punctuation noise
- isolated symbols or stray glyphs

So the tradeoff was clear: tiling dramatically improved recall, but it also
increased cleanup work.

#### Post-OCR VL backend comparison

On the same whole-page workbook, the post-OCR VL backends differed mainly in
how much artifact cleanup they achieved after the strong base pipeline.

Artifact-entry totals were:

- `PaddleOCR (No VL)`: `228`
- `Deepseek`: `228`
- `olmOCR`: `177`
- `Chandra`: `164`
- `PaddleVL`: `130`
- `ABBYY`: `211`

The most important pattern here is that `PaddleVL` produced the cleanest
overall Paddle output by this workbook's artifact-counting method. `Chandra`
was the next best cleanup backend, then `olmOCR`. `DeepSeek` did not improve
the artifact total over the raw tiled run in this comparison.

![Whole-page artifact totals](test-results/plots/png/artifact_totals.png)

It is also notable that ABBYY was not artifact-free. The workbook still tags
ABBYY with reading-order issues, suspicious glyphs, punctuation artifacts, and
spacing problems. The difference is that ABBYY generally avoided the very large
coverage loss seen in the preprocess-only Paddle run, while also avoiding as
many duplicate or tiled-overlap artifacts as the raw tiled Paddle output.

#### Human-transcription comparison

The workbook
[test-results/first_article_ocr_comparison.xlsx](test-results/first_article_ocr_comparison.xlsx)
shows a slightly different ranking when the target is a normalized human
transcription of the first article rather than whole-page artifact counts.

In this section:

- `Word accuracy` is the share of human-reference words recovered correctly
  after normalization
- `WER` means word error rate: word edit distance divided by the human word
  count, so lower is better
- `CER` means character error rate: character edit distance divided by the
  human character count, so lower is better

These metrics do not tell exactly the same story. `WER` is usually the most
useful measure for readable transcription quality, because it penalizes wrong,
missing, or inserted words directly. `CER` is more fine-grained: it can stay
fairly low even when a model still makes important word-level mistakes such as
splits, joins, or near-miss substitutions. `Word accuracy` is easier to read
quickly, while `WER` is the more standard error metric.

Ranked by normalized word error rate:

1. `ABBYY`
   Word accuracy `96.58%`, WER `3.42%`, CER `1.93%`
2. `Chandra`
   Word accuracy `94.34%`, WER `5.66%`, CER `1.75%`
3. `PaddleVL`
   Word accuracy `94.23%`, WER `5.77%`, CER `2.37%`
4. `DeepSeek`
   Word accuracy `93.38%`, WER `6.62%`, CER `1.60%`
5. `PaddleOCR (No VL)` base run
   Word accuracy `92.95%`, WER `7.05%`, CER `1.55%`
6. `olmOCR`
   Word accuracy `90.60%`, WER `9.40%`, CER `4.19%`

The human first-article reference contains `936` words. Comparing raw output
lengths is not the same as comparing transcription quality, but it is still a
useful quick check for under- or over-production against that target.

![First-article word counts](test-results/plots/png/human_word_counts.png)

This means ABBYY remained the best overall article transcription in the current
tests, but the strongest Paddle-centered results were close enough to be worth
careful comparison rather than dismissal.

![Human-transcription WER vs CER](test-results/plots/png/human_tradeoffs.png)

`olmOCR` is the visual outlier in this chart because it performs worse on both
axes at once. It has the highest `WER` and also by far the highest `CER`,
which means it is not only making more word-level mistakes, but also making
heavier character-level distortions inside those words and lines. In this
excerpt, `olmOCR` shows more severe substitutions, merged or split words, and
line-level corruption such as `colonies has afforded` becoming `The nies rising
has afforded`, `monarchical system` becoming `chemicals system`, and
`themselves by the departure` becoming `a) 18 1777 by the departure`. So its
position on the chart reflects both higher error volume and more disruptive
error types than the other Paddle-centered runs.

Three details stand out:

- `Chandra` is slightly ahead of `PaddleVL` on both word accuracy and WER,
  and it also has the better CER, so it produced the stronger article-level
  result of the two in this specific excerpt
- `Chandra` and `PaddleVL` remain the strongest Paddle-centered runs by WER,
  but `DeepSeek` and the base `PaddleOCR (No VL)` run now have the lowest CER
  among the Paddle variants
- several Paddle variants still have lower CER than ABBYY while also having worse
  WER, which suggests many remaining Paddle errors are word-level substitutions,
  joins, or segmentation mistakes rather than uniformly bad character reading

#### Conclusions

The results suggest a set of conclusions:

- preprocessing helped, but was nowhere near sufficient by itself
- tiling the source image into a `3x2 grid + PP-DocLayoutV3` tiles was the decisive recall improvement
- post-OCR VL correction mattered mainly as a cleanup stage on top of that
  stronger base pipeline
- `PaddleVL` gave the best whole-page cleanup by artifact counts
- `Chandra` and `PaddleVL` gave the strongest first-article word-accuracy
  results among the Paddle-centered variants
- `ABBYY` still had the best overall transcription quality in the current test

So the main gap between raw Paddle OCR and ABBYY on this page was first a coverage problem, then a cleanup problem. 

Tiling plus layout parsing solved the first problem. The remaining differences were mostly about how well each follow-up backend corrected the noise introduced by tiling strategies and base PaddleOCR model.

The main lesson is that ABBYY vs Paddle is not just a model-vs-model comparison. It is usually a platform-vs-pipeline-stack comparison. If you want Paddle to get closer to ABBYY, the gap to close is usually not only "better OCR." It is a bundle of surrounding capabilities:

- stronger preprocessing
- stronger layout analysis
- better pipeline routing
- more structure-aware extraction
- stricter validation
- safe human-review escalation
- cleaner export normalization

So if ABBYY outperforms a model on a document, the difference may come from any
combination of recognition quality, layout analysis, field constraints,
validation logic, or workflow-level post-processing, not just from better raw
character classification.

#### What ABBYY does around the document that Paddle users would need to recreate

If the goal is to get Paddle closer to ABBYY-quality end-to-end OCR on difficult
documents, it is not enough to compare ABBYY against a Paddle's bare OCR recognizer.
ABBYY's own document-processing pages describe several surrounding stages that
materially affect recognition quality and output quality.

##### Image enhancement before OCR

ABBYY explicitly says it improves document images before recognition. On its
current Document AI pages, this includes correcting distortions from mobile
cameras, handling poor lighting, and separating text from noisy or patterned
backgrounds, field markings, guides, lines, and protection marks. Its OCR SDK
pages also describe traditional preprocessing functions such as rotation,
binarization, and de-skewing.

To make Paddle more comparable, you would want to recreate a preprocessing
layer that can do at least some of the following:

- page rotation and orientation correction
- de-skewing or geometric correction
- perspective correction / unwarping
- contrast normalization
- denoising and background suppression
- border removal and crop cleanup
- binarization or adaptive thresholding where useful
- line / guide / form-mark suppression when those elements hurt OCR

This is one of the biggest reasons a commercial platform can outperform a raw
open OCR run on messy documents: the recognizer may be seeing a much better
image.

##### Full document analysis, not just text detection

ABBYY says it analyzes both the page layout and the logical structure of the
document. Its OCR SDK documentation specifically mentions text blocks, tables,
table cells, pictures, barcodes, separators, page orientation, double pages,
vertical text, and non-relevant areas that should be ignored.

To approximate that in Paddle, you would need more than text detection. You
would also need:

- layout region detection
- non-text region suppression
- table detection and reconstruction
- reading-order recovery
- header / footer / marginalia handling
- region-specific OCR decisions

Without that layer, Paddle may read the right characters locally but still
produce weaker page-level output because the page structure was handled less
well.

##### Document classification and routing

ABBYY's current OCR/ICR and data extraction pages describe classification as a
separate step: the system analyzes both image and text features, determines the
document type, and routes the document to the appropriate extraction model.

To recreate that behavior with Paddle, you would need a routing layer that can
decide questions like:

- is this page better handled by `PP-OCR`, `PP-Structure`, or `PaddleOCR-VL`
- is this document a form, article page, ID, invoice, or something else
- should table parsing or layout-heavy parsing be enabled
- should different preprocessing or decoding settings be applied to this class

Without routing, Paddle is often evaluated as one fixed pipeline against ABBYY's
adaptive workflow, which is not an equal comparison.

##### Field-aware extraction instead of plain text dumping

ABBYY's public materials emphasize that OCR and ICR feed extraction. It is not
only recognizing text; it is recognizing text in the context of expected
document fields, tables, checkmarks, barcodes, signatures, and related business
elements.

To get closer with Paddle, you would need application-level logic that can:

- identify which regions correspond to target fields
- choose the right parser for those regions
- preserve table and form structure
- normalize output into field/value representations instead of only free text

Raw OCR text can look worse than ABBYY even when the characters are similar, simply because ABBYY is reconstructing structured results rather than emitting a flat stream.

##### Validation and constraint checking after recognition

ABBYY explicitly describes a validation stage where extracted data is checked
against predefined rules and external databases, with human review for more
complex cases.

To recreate that quality layer around Paddle, you would need post-processing
such as:

- regex and format validation
- allowed-character or dictionary checks
- cross-field consistency rules
- database or lookup-table verification
- confidence thresholds that trigger review instead of silent acceptance

This does not improve the raw OCR model directly, but it improves practical
output quality by catching bad reads before they become final data.

##### Human review for uncertain cases

ABBYY's pipeline includes human-in-the-loop review and continuous learning from
corrections. That matters because a production-quality result is not only about
high average accuracy. It is also about safely handling the pages the model is
not confident about.

To match that with Paddle, you would likely need:

- confidence scoring or heuristics for escalation
- a review UI or annotation loop
- corrected-output capture
- a feedback path for improving prompts, preprocessing, routing, or training

If ABBYY produces fewer bad final outputs, part of the reason may be that it is
designed to stop and ask for help when confidence is low.

##### Export and reconstruction logic

ABBYY's OCR SDK pages emphasize exact or high-quality reconstruction of the
document's structure and formatting. That means the final output is shaped by
layout recovery and export logic, not only by text recognition.

To reproduce that with Paddle, you may need additional code for:

- reading-order reconstruction
- block merging and region cleanup
- Markdown / JSON / ALTO shaping
- table serialization
- page-level normalization before TXT export
- PDF creation (Including PDF/A - 1a)

This is especially important in this repo because evaluation quality can be ffected by formatting artifacts, not just by recognition mistakes.

## Analysis And Helper Scripts

### Comparison Tool

The repo includes [tools/compare_ocr_errors.py](tools/compare_ocr_errors.py) for
Paddle-vs-ABBYY review.

Single-file CSV mode:

```bash
python tools/compare_ocr_errors.py \
  --paddle path/to/paddle.txt \
  --abbyy path/to/abbyy.txt \
  --output path/to/errors.csv
```

Folder-to-folder Excel mode:

```bash
python tools/compare_ocr_errors.py \
  --paddle-dir test-results/paddlecomp \
  --abbyy-dir "test-results/large - abby" \
  --excel-output test-results/paddle_vs_abbyy_errors_artifacts.xlsx
```

Current Excel behavior:

- one worksheet per matching Paddle TXT file
- if the target workbook already exists, the script reuses the existing sheet names, freeze panes, column widths, and row heights


### Human Comparison Workbook

[tools/compare_ocr_to_human.py](tools/compare_ocr_to_human.py) compares a human transcription against ABBYY plus every `first-article.txt` found under `test-results/paddlecomp`, then writes a shareable Excel workbook.

Example:

```bash
python tools/compare_ocr_to_human.py \
  --human "test-results/large - human/first-article.txt" \
  --abbyy "test-results/large - abby/first-article.txt" \
  --paddlecomp-dir test-results/paddlecomp \
  --output-dir test-results \
  --prefix first_article_ocr_comparison
```

### Plotly visualizations

The comparison workbooks are easier to interpret when graphed. The repo 
includes [tools/generate_ocr_plots.py](tools/generate_ocr_plots.py), which
reads the two Excel workbooks and builds a Plotly HTML dashboard:

- [test-results/plots/ocr_evaluation_dashboard.html](test-results/plots/ocr_evaluation_dashboard.html)
- PNG exports under [test-results/plots/png](test-results/plots/png)

The HTML dashboard renders the full chart set in English first and then again
in French.

Generate or refresh it with:

```bash
python tools/generate_ocr_plots.py
```

The dashboard includes several useful views of the data:

- whole-page line recovery
  shows how closely each workflow matched ABBYY's line-level coverage
- whole-page word recovery
  shows why preprocess-only failed and why `PaddleOCR (No VL)` became the base
  pipeline
- whole-page word counts
  shows the absolute word totals returned by ABBYY and each Paddle-based
  workflow
- first-article word counts
  shows the human-reference word count plus ABBYY and each Paddle-based
  transcription, sorted from low to high
- whole-page artifact totals
  compares cleanup quality across the post-OCR VL backends against the ABBYY
  baseline
- artifact-category vs ABBYY small multiples
  shows each Paddle workflow separately, with every artifact category expressed
  as a percent of ABBYY's count for that same category
- human-transcription WER/CER scatter
  shows article-level quality tradeoffs between word error rate and character
  error rate
- human-transcription edit breakdown
  separates substitutions, insertions, and deletions so backend differences are
  easier to interpret
