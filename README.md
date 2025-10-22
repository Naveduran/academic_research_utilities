# Academic Paper Processing CLI Tool

A unified command-line tool for processing academic papers with multiple subcommands.

## Installation

```bash
pip install PyPDF2 pdfplumber requests beautifulsoup4 PyMuPDF
```

## Usage

```bash
python academic_papers_cli.py <command> [options]
```

### Available Commands

#### Convert PDFs
```bash
python academic_papers_cli.py convert-pdf <input_path> <output_dir> [--clean]
```
Converts PDF files to plain text using multiple extraction methods. Essential first step for text analysis, as all other commands require plain text files. Handles complex layouts and maintains folder structure for batch processing.

#### Extract References
```bash
python academic_papers_cli.py extract-references <input_dir> <output_file>
```
Extracts bibliographic metadata (DOI, authors, title, year, webpage) from academic papers previously converted to txt files. Useful for building reference databases, citation analysis, and creating structured bibliographies from large document collections.

#### Extract Emails
```bash
python academic_papers_cli.py extract-emails <input_dir> <output_file>
```
Finds and consolidates email addresses from academic papers. Valuable for building researcher contact databases, identifying corresponding authors, and facilitating academic networking and collaboration.

#### Enrich Metadata
```bash
python academic_papers_cli.py enrich-metadata <input_file> <output_file> --api-key <key> --cse-id <id> [--delay <seconds>]
```
Enhances reference data with additional metadata (abstracts, author details, web sources) using DOI resolution and Google search. Automatically analyzes processing results and provides quality statistics. Critical for comprehensive literature reviews and research gap analysis.

**Setup Google API credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Custom Search JSON API"
4. Create credentials (API Key)

**Get Search Engine ID:**
1. [Create a new Custom Search Engine (CSE)](https://cse.google.com/cse/create/new)
2. Select "Search the entire web"
3. Click "Create"
4. Copy the "Search engine ID" from https://programmablesearchengine.google.com/controlpanel/all

#### Make PDF Highlightable
```bash
python academic_papers_cli.py make-highlightable <input_path> <output_dir>
```
Creates annotation-enabled PDF copies for research workflows. Processes single files or entire directories while maintaining folder structure. Enables highlighting, note-taking, and markup in PDF readers, essential for active reading and collaborative research annotation.

## Features

- **Batch Processing**: Optimized for processing entire folders of academic papers
- **Portable**: All file paths are configurable via command-line arguments
- **Proper Error Handling**: Comprehensive error checking and meaningful error messages
- **Modular Architecture**: Each command is implemented as a separate class
- **Logging**: Built-in logging with configurable verbosity
- **Structure Preservation**: Maintains folder hierarchy during batch operations

## Typical Research Workflow

```bash
# 1. Convert PDFs to text (foundation step)
python academic_papers_cli.py convert-pdf ./pdfs ./text_output --clean

# 2. Extract references for bibliography
python academic_papers_cli.py extract-references ./text_output ./references.txt

# 3. Extract researcher contacts
python academic_papers_cli.py extract-emails ./text_output ./contacts.txt

# 4. Enrich with additional metadata (includes automatic analysis)
python academic_papers_cli.py enrich-metadata ./references.txt ./enriched.txt --api-key YOUR_KEY --cse-id YOUR_CSE_ID

# 5. Create highlightable PDFs for annotation
python academic_papers_cli.py make-highlightable ./pdfs ./highlightable_pdfs
```