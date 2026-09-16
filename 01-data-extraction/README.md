# Literature extraction

The pipeline searches Crossref, filters candidate papers, downloads available
PDFs, and extracts copolymerization measurements with a vision–language model.
[obtain_data.py](obtain_data.py) coordinates the modules in
[src/copolextractor](../src/copolextractor/).

## Run

Install the `extraction` extra from the repository root. Configure paths and
thresholds in `ExtractionConfig`, and select stages through `ExtractionSteps`
in `obtain_data.py`, then run:

```bash
uv run --locked --extra extraction python 01-data-extraction/obtain_data.py
```

By default, extraction and CSV export are enabled. Extraction calls the paid
OpenAI API; it requires credentials and local PDFs. Enable search, relevance
filtering, and downloading explicitly for a new literature collection.

The downloader queries open-access sources. It writes unresolved DOIs to
`unresolved_papers.json` in the configured PDF folder and pauses for manual
collection. Place the remaining PDFs there before continuing, or set
`pause_for_manual_pdf_download=False` to process only the available files.

## Stages and outputs

| Module in `src/copolextractor` | Stage |
|---|---|
| `crossref_search.py` | Literature search and metadata |
| `predownloadfilter/` | Keyword and embedding relevance filters |
| `PDF_download.py` | PDF download |
| `preextractionfilter/` | Document quality assessment |
| `extraction_with_GPT_PDF.py` | Vision–language extraction |
| `data_into_csv.py` | Consolidation and CSV export |

Fresh runs write intermediates under `01-data-extraction/artifacts/`.
[provenance](provenance/README.md) preserves records from the released extraction;
`archive/` holds earlier experiments.

The released CSV is [src/copolextractor/extracted_reactions.csv](../src/copolextractor/extracted_reactions.csv).
The [prediction pipeline](../02-reactivity-prediction/copol_prediction/README.md)
preprocesses these measurements into `processed_data.csv`. To reproduce the
paper's model results, use the bundled data and
[reproduction guide](../REPRODUCIBILITY.md).
