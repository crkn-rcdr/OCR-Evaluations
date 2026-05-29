# Assessing AI-Powered OCR Tools

A repo containing data for analyzing the open-source PaddleOCR engine along with PaddleVL, olmOCR, Chandra, or Deepseek VL models for low confidence word correction vs ABBYY FineReader Server 14 on difficult historical newspaper pages and multi-document OCR sets.

The repo contains both:

- single-page and stress-test style experiments
- multi-document comparisons across `3x2` tiling, `3x1` tiling, and no-tiling runs

## Dataset Layout

- [1-stress-test](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\1-stress-test)  
  Single-page stress test and helper tooling.
- [2-multi-document-abbyy-vs-tiled3x2+docparse-paddleocr-paddlevl](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\2-multi-document-abbyy-vs-tiled3x2+docparse-paddleocr-paddlevl)  
  Multi-document ABBYY vs tiled `3x2` analysis.
- [3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl)  
  Multi-document ABBYY vs tiled `3x1` analysis.
- [4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl)  
  Multi-document ABBYY vs no-tiling analysis and the canonical cross-run recommendation.

## Project Context

This repo is not only comparing OCR recognizers. It is usually comparing:

- `ABBYY` as an integrated commercial document-processing platform
- `Paddle` as a configurable open-source OCR and document-parsing stack

That distinction matters, because output quality can depend on much more than raw character recognition:

- image enhancement
- layout detection
- reading-order recovery
- field-aware extraction
- validation rules
- human review workflows
- export normalization


## How ABBYY OCR/ICR Works

The notes below summarize ABBYY's public product documentation reviewed on
May 26, 2026, with emphasis on the OCR/ICR pipeline that matters when using
ABBYY as a benchmark in this repo.

ABBYY does more than basic text recognition. Its current positioning is
"Document AI" or intelligent document processing (IDP): OCR and ICR are the
core recognition steps inside a larger workflow that also includes image
cleanup, document structure analysis, classification, data extraction,
validation, human review, and export into machine-readable formats.

### 1. Document input and image enhancement

ABBYY first tries to improve the input image before recognition. According to
its product pages, this stage is meant to deal with low-quality scans and
camera photos, including distortion, uneven lighting, noisy backgrounds,
patterned forms, guides, and protection marks. The goal is to separate useful
text from the background and hand a cleaner image to the recognizer, which is
important for difficult business documents such as IDs, certificates, and
forms.

### 2. Layout and document analysis

Before or alongside character recognition, ABBYY analyzes the page structure.
Its OCR SDK documentation describes detecting the logical and visual layout of
the document: text blocks, pictures, tables, table cells, barcodes, separators,
orientation, double pages, vertical text, headers, footers, and other
formatting elements. This step is what lets ABBYY preserve structure instead of
returning only a flat text dump.

### 3. OCR for printed text

ABBYY uses OCR for machine-printed text. On its official pages, ABBYY states
that its OCR supports more than 200 languages and is designed for both full
document conversion and field extraction. The engine is intended to work on
complex documents, not just simple paragraphs, so tables, mixed layouts, and
special fonts are part of the intended use case.

ABBYY OCR should be thought of as a combination of:

- image preprocessing
- page segmentation and layout detection
- character and word recognition
- structural reconstruction for export

That is one reason ABBYY outputs often look more organized than a raw OCR text
stream from simpler pipelines.

### 4. ICR for hand-printed text

ABBYY treats ICR as a specialized extension of OCR for hand-printed characters.
Its support docs distinguish this from cursive handwriting: ICR is intended for
letters or digits written as separate printed characters in fields or zones,
such as form entries, boxed values, or constrained handwriting areas. ABBYY
also notes that ICR is commonly tied to field-level or zonal recognition rather
than unconstrained full-page handwriting transcription.

### 5. Field-level recognition and extraction

ABBYY's own documentation separates full-text recognition from field-level
recognition. Full-text mode is for document conversion or archiving. Field-level
mode is for pulling specific values from forms and business documents.

In field-level extraction, ABBYY can combine several techniques:

- OCR for printed fields
- ICR for hand-printed fields
- barcode recognition
- checkmark/mark recognition
- constraints such as alphabets, dictionaries, regular expressions, and
  expected value patterns

This is a major reason ABBYY often performs well on operational documents. It
is not only "reading text"; it is using document context and field expectations
to reduce ambiguity.

### 6. Classification and routing

On the current ABBYY Document AI pages, OCR/ICR feeds a broader classification
step. ABBYY says it uses AI models that analyze both text and image features to
classify and organize documents, then route each document to the appropriate
extraction model.

So the pipeline is roughly:

1. ingest document
2. enhance image
3. analyze structure and read content
4. classify the document type
5. apply the extraction model suited to that type

This is important because extraction quality depends heavily on identifying what
the document actually is before deciding which fields to pull.

### 7. Validation and quality control

ABBYY's data extraction materials emphasize that recognized data is then checked
against predefined rules and, when needed, external data sources or databases.
This validation layer is part of how ABBYY turns OCR output into something more
usable for business workflows.

Examples of validation logic include:

- expected formats for dates, invoice numbers, or IDs
- allowed character sets
- cross-field consistency checks
- matching against known records or reference systems

For ICR specifically, ABBYY's support guidance also recommends using regular
expressions, dictionaries, or database lookups to improve recognition accuracy.

### 8. Human in the loop and continuous learning

ABBYY describes an optional human review stage for cases where confidence is too
low or business rules require manual confirmation. Reviewers can correct
document classes and extracted values through a validation interface. ABBYY's
current product pages say those corrections feed continuous learning so the
models improve over time.

Operationally, this means ABBYY is designed for high straight-through
processing, but not on the assumption that every page can be handled with zero
review. The system is built to escalate uncertain cases instead of silently
accepting bad data.

Sources:

- https://www.abbyy.com/ai-document-processing/ocr-icr/
- https://www.abbyy.com/ai-document-processing/data-extraction-and-validation/
- https://www.abbyy.com/ocr-sdk/ 
- https://www.abbyy.com/ocr-sdk/how-it-works/document-analysis/
- https://www.abbyy.com/ocr-sdk/features/ocr/
- https://help.abbyy.com/en-us/finereader/15mac/user_guide/preprocess/
- https://intuitionlabs.ai/articles/non-llm-ocr-technologies
- https://help.abbyy.com/assets/en-us/finereader/16/Users_Guide.pdf
- https://support.abbyy.com/hc/en-us/articles/360020669679-Specifications-for-FineReader-PDF-for-Mac
- https://intuitionlabs.ai/articles/non-llm-ocr-technologies

## How Paddle Works

The notes below summarize Paddle's official documentation reviewed on
May 26, 2026, focusing on the parts most relevant to this repo:
PaddleOCR, PP-OCR, PP-Structure, PaddleOCR-VL, the `doc_parser` pipeline, and
PaddleX.

At a high level, Paddle is not one single OCR model. It is a stack:

- `PaddleX` provides the broader pipeline framework, packaging, inference, and
  deployment layer
- `PaddleOCR` provides OCR-focused pipelines and models
- `PP-OCR` is the general OCR pipeline for reading text
- `PP-Structure` is the structured document parsing pipeline for layouts,
  tables, formulas, charts, and reading order
- `PaddleOCR-VL` is the newer vision-language document parsing pipeline exposed
  through `doc_parser`

### 1. PaddleX as the orchestration layer

According to Paddle's official docs, PaddleOCR reuses PaddleX for inference
deployment, pre-processing, post-processing, model composition, and service
deployment. In practical terms, PaddleX is the workflow and infrastructure
layer that helps combine multiple models into a usable pipeline.

That means PaddleX is doing several important jobs under the hood:

- registering named pipelines such as `OCR`, `PP-StructureV3`,
  `doc_preprocessor`, and `PaddleOCR-VL`
- managing model loading and default configuration
- handling multi-model execution and post-processing
- supporting service-oriented deployment and high-performance inference
- keeping pipeline naming and configuration consistent across CLI and Python

### 2. PaddleOCR / PP-OCR: the general OCR pipeline

PaddleOCR's general OCR pipeline is the modular text-reading path. The official pipeline docs describe five stages:

1. optional document image orientation classification
2. optional text image unwarping / rectification
3. optional text-line orientation classification
4. text detection
5. text recognition

The current PaddleOCR 3.x docs say this pipeline supports PP-OCRv3, PP-OCRv4,
and PP-OCRv5, with PP-OCRv5 as the default in current releases.

Conceptually, PP-OCR works like this:

- find where text exists on the page
- crop or normalize those text regions
- recognize each text line or block
- assemble the recognized strings into output text plus coordinates

This modular design is important because the OCR result is influenced by more
than the recognizer itself. Rotation handling, unwarping, text detection, and
line orientation correction can all change final accuracy.

PP-OCR does give word level content boxes.

For our experiment, we used [PP-v5OCR](https://huggingface.co/collections/PaddlePaddle/pp-ocrv5).

#### What PP-OCR is good at

PP-OCR is the right Paddle family component when the main task is:

- reading machine-printed text from images or PDFs
- extracting text with bounding boxes
- building a fast, modular OCR pipeline
- swapping detection or recognition models for speed vs accuracy tradeoffs

It is closer to a classical OCR pipeline than a general-purpose multimodal
model. That usually makes it lighter and easier to reason about, but it also
means document structure has to be handled by additional pipelines when the
page is complex.

### 3. PP-Structure: document layout parsing and structure recovery

PP-Structure is Paddle's structured document analysis pipeline. The current
PP-StructureV3 docs describe it as a layout analysis pipeline that combines OCR,
image processing, and machine learning to convert complex document layouts into
machine-readable structured data.

The official PP-StructureV3 pipeline includes these major modules or
sub-pipelines:

- layout detection
- general OCR
- optional document image preprocessing
- optional table recognition
- optional seal text recognition
- optional formula recognition
- optional chart parsing

Paddle also states that PP-StructureV3 strengthens layout region detection,
table recognition, and formula recognition, while adding multi-column reading
order recovery, chart understanding, and conversion to Markdown.

In practice, PP-Structure is answering questions that plain OCR does not solve
well:

- where are the text blocks, titles, tables, figures, formulas, and seals
- what order should multi-column or mixed-layout content be read in
- how should tables be reconstructed instead of flattened into plain text
- how should the final output preserve hierarchy and structure

For repo comparisons, PP-Structure is the Paddle component most analogous to
the structure-preserving part of ABBYY's document workflow.

PP-Structure does not give word level content boxes.

### 4. Paddle DocParser / PP-DocLayoutV3: the PaddleOCR-VL document parsing pipeline

In current PaddleOCR 3.x docs, `doc_parser` is the CLI/API-facing document
parsing pipeline tied to `PaddleOCR-VL`. It is not just another name for
general OCR. It is the newer VLM-based path for richer page understanding.

The PaddleOCR-VL usage docs explicitly say the full pipeline matters. Paddle
describes the process in two broad stages:

1. layout analysis splits the page into document elements and determines
   reading order
2. VLM-based recognition processes each sub-image or element and produces
   structured output such as Markdown, after which element outputs are merged
   back into a full-page result

The docs also warn that using only the VLM component is not equivalent to using
the full PaddleOCR-VL pipeline. In other words, the quality depends on the
complete system, not just the language-vision model weights.

The `doc_parser` examples in the official docs show that this pipeline can be
configured with options such as:

- document orientation classification
- document unwarping
- layout detection on or off
- pipeline version selection such as `"v1"` and `"v1.5"`

So "Paddle PP-DocLayoutV3r" is best understood as Paddle's structured document
parsing entry point, powered by the PaddleOCR-VL family and surrounding layout
logic.

### 5. PaddleOCR-VL: VLM-based parsing instead of only OCR

([PaddleOCR-VL-1.5-0.9B](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5)) 

PaddleOCR-VL is Paddle's newer vision-language document parsing model family.
The current official introduction describes it as a resource-efficient document
parsing model whose core component is a compact VLM that combines:

- a NaViT-style dynamic-resolution visual encoder
- the ERNIE-4.5-0.3B language model

The docs say PaddleOCR-VL supports 109 languages and is intended for complex
document element recognition, including:

- text
- tables
- formulas
- charts

The current usage docs also frame it as a full parsing system rather than only
a recognizer. Its job is not simply to emit text tokens. It tries to identify
elements, recognize them appropriately, preserve reading order, and produce
structured document output.

This is a meaningful shift from PP-OCR:

- `PP-OCR` is primarily OCR-first and modular
- `PP-Structure` adds explicit document structure parsing around OCR modules
- `PaddleOCR-VL` moves further toward end-to-end vision-language document
  parsing

For difficult pages, that can make PaddleOCR-VL stronger than a plain OCR stack,
but it also means more complexity, heavier inference, and different failure
modes such as hallucinated structured text if the pipeline is misused.

PaddleOCR-VL also does not give word level content boxes.

Sources:

- https://www.paddleocr.ai/main/en/index.html
- https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/OCR.html
- https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html
- https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL.html
- https://www.paddleocr.ai/latest/en/version3.x/algorithm/PaddleOCR-VL/PaddleOCR-VL.html
- https://www.paddleocr.ai/main/en/version3.x/paddleocr_and_paddlex.html
- https://www.paddleocr.ai/main/en/version3.x/paddlex/overview.html

## ABBYY vs Paddle

This section compares ABBYY against Paddle as they are most relevant to this repo. "Paddle" here does not mean one thing: it can mean `PP-OCR`, `PP-Structure`, or `doc_parser` / `PaddleOCR-VL`, all orchestrated through `PaddleX`.

### High-level difference

At a high level, ABBYY is a commercial document processing platform with OCR or ICR embedded inside a broader validation and workflow system. Paddle is an open-source model and pipeline stack that gives you several document-reading paths, but generally expects more explicit configuration and evaluation work from the user.

That leads to a practical distinction:

- ABBYY is usually opinionated and workflow-oriented
- Paddle is usually modular and engineering-oriented

### Where ABBYY is stronger

ABBYY tends to be stronger when the document problem is not only "read the text" but "extract reliable business data from messy documents with controls."

Its advantages include:

- strong layout and field-aware extraction behavior
- built-in validation concepts such as rules, dictionaries, expected formats,
  and external record checks
- a more integrated path from ingestion to structured output
- mature commercial OCR and ICR focused on business documents
- optional human review workflows for uncertain cases

In other words, ABBYY often wins by combining recognition with structure, constraints, and workflow-level quality control.

### Where Paddle is stronger

Paddle tends to be stronger when you want openness, flexibility, and control over how the OCR stack is assembled.

Its advantages include:

- open-source access to models and pipelines
- easier experimentation across OCR-first and VLM-based approaches
- direct control over preprocessing, layout analysis, and pipeline selection
- easier integration into custom research or engineering workflows without a
  commercial platform dependency

In this repo specifically, Paddle is useful because it exposes more of the pipeline knobs that can be tuned, swapped, or inspected during benchmarking.

### OCR philosophy: integrated platform vs modular stack

ABBYY and Paddle are solving related problems, but they package the solution very differently.

ABBYY behaves more like an integrated platform:

- image cleanup
- layout understanding
- OCR and ICR
- extraction
- validation
- human review
- export into downstream workflows

Paddle behaves more like a toolkit with multiple tiers:

- `PP-OCR` for modular OCR
- `PP-Structure` for structured document parsing
- `PaddleOCR-VL` for VLM-based parsing
- `PaddleX` for pipeline orchestration and deployment

That means ABBYY usually presents a more unified workflow, while Paddle gives you more freedom to choose which pipeline style to run.

### Structured documents

Both ABBYY and Paddle care about document structure, but they get there differently.

ABBYY's structure handling is part of a business-document platform and is tied closely to extraction and validation. 

Paddle splits the problem into separate pipelines:

- `PP-OCR` for raw text reading
- `PP-Structure` for layout-aware structured parsing
- `PaddleOCR-VL` for richer VLM-based parsing

So if Paddle underperforms ABBYY on a complex page, the reason may simply be that the comparison used `PP-OCR` when the more appropriate Paddle baseline was `PP-Structure` or `PaddleOCR-VL`.

### Handwriting and ICR

ABBYY can support ICR for structured hand-printed text fields. That is important for forms, boxed entries, and constrained handwriting zones.

Paddle 3.x documentation explicitly describes pipelines as improving recognition for multiple text types, including handwriting, and the PaddleOCR model and pipeline family includes handwriting-relevant recognition support in addition to printed-text OCR. 

PaddleOCR-VL also broadens this further by using a document VLM that can recognize and parse more varied document content than a classical printed-text-only OCR stack.

The more accurate distinction is narrower: ABBYY's product framing is still more explicitly tied to structured business-document ICR for constrained hand-printed fields, while Paddle's current public framing is broader handwriting/HTR-aware OCR and document parsing rather than ABBYY-style field-oriented ICR as a first-class product concept. 

So if a benchmark depends heavily on boxed hand-printed field extraction, ABBYY may still have an advantage in product design and workflow assumptions, even though Paddle is not limited to printed-text-only OCR.

### Validation and trust model

One of the biggest differences is what happens after text is recognized.

ABBYY emphasizes:

- field constraints
- validation rules
- reference checks
- reviewer escalation
- continuous learning from corrections

Paddle emphasizes:

- model inference
- pipeline composition
- structured outputs
- developer-controlled post-and-pre-processing

So ABBYY is more likely to ship with business-process guardrails already in
mind, while Paddle is more likely to require custom downstream logic if you
need the same level of validation discipline.

### Failure modes

The two stacks can fail for different reasons.

ABBYY failure modes are often tied to:

- weak scan quality
- unusual layouts outside trained business-document expectations
- hard handwriting cases outside constrained ICR use
- extraction rule mismatches

Paddle failure modes vary by pipeline:

- `PP-OCR` can miss structure because it is fundamentally OCR-first
- `PP-Structure` can still depend heavily on layout detection quality
- `PaddleOCR-VL` can introduce VLM-style errors, including incorrect structured
  reconstruction or over-generated text if the full pipeline is not used well

So a fair comparison should identify not just whether output is wrong, but what kind of system design issue caused the discrepancy.

### Cost and control

ABBYY usually offers more packaged functionality out of the box, but that comes
with commercial product constraints and high licensing costs.

Paddle usually offers:

- lower barriers to experimentation
- source-level visibility
- easier custom deployment paths
- more direct control over the stack

But that flexibility also means the user has to make more decisions about
pipeline selection, preprocessing, evaluation methodology, and post-processing. One might also need development skills.

## PaddleVL vs olmOCR, DeepSeek, and Chandra

During the expirement, we also used the following alternative VL libraries:

- `olmOCR` ([olmocr2:7b-q8](https://ollama.com/richardyoung/olmocr2)) is a PDF-to-text linearization and extraction toolkit
- `Chandra` ([chandra-ocr-2](https://ollama.com/fredrezones55/chandra-ocr-2)) is an OCR-oriented structured document model
- `DeepSeek OCR` ([deepseek-ocr:3b](https://ollama.com/library/deepseek-ocr:3b)) is an end-to-end OCR and document-to-markdown model built
  around visual-text compression

### PaddleVL vs olmOCR

`PaddleVL` and `olmOCR` both go beyond raw text extraction, but they are aimed
at different outcomes.

`olmOCR` is described by Ai2 as an open toolkit for converting
PDFs into clean linearized plain text in natural reading order while preserving
structured content such as sections, tables, lists, and equations. Its paper
describes a fine-tuned 7B VLM trained on a large PDF-derived dataset and
optimized for large-scale batch PDF processing.

- `PaddleVL` is more naturally positioned for multilingual page parsing with
  richer element recognition
- `olmOCR` is more naturally positioned for scalable PDF-to-text extraction and
  reading-order recovery

If the target is structured page understanding across many languages,
`PaddleVL` has the clearer specialization. If the target is high-throughput
PDF linearization into clean text, `olmOCR` has the clearer specialization.

### PaddleVL vs DeepSeek OCR

`PaddleVL` and `DeepSeek OCR` are both VLM-style document systems, but their
technical framing is different.

`DeepSeek-OCR` is framed by DeepSeek as "Contexts Optical Compression." Its
official repo and model card position it as an end-to-end OCR system that can
do plain OCR or convert a document directly to Markdown. The emphasis is on
visual-text compression and token-efficient document understanding before
decoding.

- `PaddleVL` looks more like a compact structured document parser
- `DeepSeek OCR` looks more like a generative OCR system optimized around
  efficient document-to-text or document-to-markdown conversion

That means `DeepSeek OCR` may be especially attractive when long documents,
token efficiency, or direct markdown generation matter. `PaddleVL` may be the
better fit when tighter layout-oriented pipeline control and multilingual
document parsing are more important.


### PaddleVL vs Chandra

`PaddleVL` and `Chandra` are more directly comparable because both are aimed at
structured document output rather than only flat OCR text.

`Chandra OCR 2` emphasizes rich OCR reconstruction. Its official model card
describes output in Markdown, HTML, and JSON with detailed layout information,
strong support for handwriting, forms including checkboxes, tables, math, and
90+ languages. Its positioning is closer to a specialized OCR-native document
reconstruction model.

- `PaddleVL` is more compact and pipeline-centric
- `Chandra` is more explicitly focused on high-fidelity structured OCR output

So this comparison is less about OCR versus VLM, and more about two different
styles of document VLM: one compact and pipeline-oriented, the other more
aggressively optimized for OCR-style structured reconstruction.

Sources:

- https://www.paddleocr.ai/latest/en/version3.x/algorithm/PaddleOCR-VL/PaddleOCR-VL.html
- https://olmocr.allenai.org/
- https://olmocr.allenai.org/papers/olmocr.pdf
- https://huggingface.co/datalab-to/chandra-ocr-2
- https://github.com/deepseek-ai/DeepSeek-OCR
- https://huggingface.co/deepseek-ai/DeepSeek-OCR


## How To Read The Counts

Many of the workbooks in this repo count `artifact entries`, not only bad lines.

One OCR line can receive more than one error tag. For example, a line might be counted as both:

- `suspicious glyph`
- `OCR token/phrase mismatch`

Because of that:

- per-type counts can add up to more than the total number of artifact entries
- a lower artifact total means fewer tagged problems overall, not necessarily fewer total lines

Word-count and token-coverage metrics tell a different story from artifact counts:

- more words captured is better when the goal is recall
- lower artifact totals are better when the goal is cleanliness
- the best workflow depends on which of those goals matters more

## Shared Error Type Guide

Below, each type is described in terms of what it means in this project and how it is interpreted across the datasets.


## How To Read The Counts

The workbook counts `artifact entries`, not just raw bad lines.

One line can receive more than one error tag. For example, a line might be counted as both:

- `suspicious glyph`
- `OCR token/phrase mismatch`

Because of that, per-type totals can add up to more than the total number of artifact entries.

## Error Type Guide

Below, each type is described in terms of what it means in this project, how the script recognizes it, and one representative example.

### 1. Duplicate / Tile Overlap

Meaning:
Content was repeated because tiled OCR regions overlapped or because adjacent lines were merged with partial duplication.

How it is detected:
The script compares each line to the previous normalized line. If similarity is high enough and enough words overlap, it marks the later line as a possible overlap duplication.

Example from this dataset:
`L406: possible duplicated/overlap line with previous line (similarity 67%) :: de Legal, et comme sous-diacre le R.`

Interpretation:
This is a Paddle-specific artifact in this run and is the clearest signature of the tiling workflow.

### 2. OCR Token / Phrase Mismatch

Meaning:
The two OCR systems disagree on a token or short phrase in a way that looks plausibly like an OCR mistake rather than a harmless spelling variant.

How it is detected:
The script aligns Paddle and ABBYY token streams and flags close but suspicious divergences, especially when one token looks less plausible or obviously malformed.

Example from this dataset:
`candidate OCR token mismatch vs other OCR: "ecueil" vs "cueil"`

Interpretation:
This category is useful when both outputs are readable but one looks like the less credible OCR rendering.

### 3. Suspicious Token

Meaning:
A token looks intrinsically wrong even before comparing against the other OCR.

How it is detected:
The script flags things like:

- odd internal casing
- letter/digit mixtures
- very long joined tokens
- word-join patterns inside one token

Example from this dataset:
`MauriCe (odd internal casing)`

Interpretation:
This category tries to catch tokens that look OCR-generated or structurally implausible.

### 4. Suspicious Glyph

Meaning:
The line contains non-ASCII characters that look like encoding debris, fullwidth/CJK symbol leakage, or other obviously wrong glyphs for the surrounding text.

How it is detected:
The script normalizes the line and flags characters that are neither allowed punctuation/accents nor likely valid text in context.

Example from this dataset:
`stray/suspicious non-ASCII glyph(s): U+02DC SMALL TILDE`

Interpretation:
ABBYY accumulated many more of these in this dataset, which suggests more encoding-style output debris in its exported text.

### 5. BOM / Control Character

Meaning:
A line begins with a byte-order mark or similar control artifact.

How it is detected:
If a line starts with `U+FEFF`, the script records a BOM/control issue.

Observed here:
No `BOM/control character` entries were recorded in this multi-document run.

Representative example form:
A first line beginning with hidden BOM text that then leaks into downstream processing.

### 6. Isolated Marker / Separator

Meaning:
The OCR emitted a line that is mostly punctuation, symbols, bullets, stars, divider fragments, or very short marker-like debris rather than meaningful text.

How it is detected:
The script flags:

- very short low-information lines
- symbol-only lines
- short marker-style lines

Example from this dataset:
`L1: symbol-only separator/garbage line :: *********`

Interpretation:
This is the dominant Paddle error type in the aggregate results. It often reflects page furniture, separators, ornament lines, or tile boundary leftovers that were preserved as text.

### 7. Punctuation Artifact

Meaning:
The line contains punctuation debris such as repeated punctuation, malformed quote/punctuation combinations, or repeated hyphens.

How it is detected:
The script checks for repeated punctuation patterns and punctuation constructions that look machine-generated rather than intentional typography.

Example from this dataset:
`L11: punctuation artifact: double/multiple hyphen :: EDMONTON, ALBERTA --`

Interpretation:
ABBYY has many more of these overall in this dataset.

### 8. Line-Start Artifact

Meaning:
The beginning of the line looks corrupted, often with punctuation glued directly to text or digit/letter garbage at the start.

How it is detected:
The script flags line starts that match patterns like:

- punctuation glued to a word
- digit-plus-letter garbage at the beginning
- lowercase prefix glued to a capitalized word

Example from this dataset:
`L237: ... line starts with digit/letter garbage token ... :: 1Canada. cernée à`

Interpretation:
This often indicates a segmentation or encoding failure at the start of a recognized line.

### 9. Spacing / Joined Text

Meaning:
Words or clauses that should be separated are fused together, or punctuation spacing is missing badly enough to change readability.

How it is detected:
The script flags patterns like:

- missing space after a period
- missing space around punctuation
- known joined-word patterns

Example from this dataset:
`L88: missing space around punctuation :: And it may be pretty safely stated,that the same rules`

Interpretation:
This was relatively uncommon in the aggregate results, especially on the Paddle side.

### 10. Abbreviation / Spacing

Meaning:
Abbreviation punctuation appears garbled, duplicated, or badly spaced.

How it is detected:
The script looks for repeated abbreviation punctuation patterns that often come from noisy OCR around initials or abbreviations.

Example from this dataset:
`L28: abbreviation/spacing may be garbled :: Il y a un peu moins de vingt ans, l'A.C.F.A.,.,`

Interpretation:
This category is distinct from general punctuation debris because it focuses on abbreviation-like constructions.

### 11. Other

Meaning:  
A fallback category for any tagged reason that does not map to the named groups above.

Interpretation:  
Usually sparse or absent, but kept for completeness.

## Where To Look Next

For run-specific analysis:

- use [1-stress-test/README.md](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\1-stress-test\README.md) for the original single-page stress test
- use [2-multi-document-abbyy-vs-tiled3x2+docparse-paddleocr-paddlevl/README.md](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\2-multi-document-abbyy-vs-tiled3x2+docparse-paddleocr-paddlevl\README.md) for ABBYY vs `3x2`
- use [3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl/README.md](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\3-multi-document-abbyy-vs-tiled3x1+docparse-paddleocr-paddlevl\README.md) for ABBYY vs `3x1`
- use [4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl/README.md](c:\Users\BrittnyLapierre\Documents\OCR-Evaluations\4-multi-document-abbyy-vs-notiles-paddleocr-paddlevl\README.md) for ABBYY vs no tiling and the canonical cross-run recommendation
