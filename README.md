# VisionCSV (Local Vision Model via Ollama)

A lightweight Python script that uses a **local multimodal AI model** through [Ollama](https://ollama.com/) to extract table data from screenshots or table images and save the result as a `.csv` file.

This project is useful when you have:

- screenshots of spreadsheets or reports
- table data trapped in images
- a need to convert visual table data into CSV quickly
- a preference for **local processing** instead of cloud OCR tools

## What the script does

The script:

1. Accepts an image file path as input
2. Sends the image to a local Ollama vision model
3. Prompts the model to return only raw CSV output
4. Cleans up markdown code blocks if the model adds them anyway
5. Saves the extracted result as a `.csv` file using the same base filename as the image

### Example

If you run the script against:

```text
sales-report.png
```

it will create:

```text
sales-report.csv
```

## Current model

The script is currently configured to use:

```python
qwen2.5vl:7b
```

You can change that in the script by editing the `MODEL` variable inside `extract_csv_from_image()`.

## Requirements

### System requirements

- Python 3.9 or newer recommended
- [Ollama](https://ollama.com/) installed and running locally
- A local vision-capable model pulled into Ollama

### Python package

This script requires:

- `ollama`

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/DeanAmiridis/VisionCSV-Local_AI.git
cd VisionCSV-Local_AI
```

### 2. Create and activate a virtual environment (recommended)

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the Python dependency

```bash
pip install ollama
```

### 4. Install Ollama

Download and install Ollama from its official site.

Then verify it is available:

```bash
ollama --version
```

### 5. Pull the required model

```bash
ollama pull qwen2.5vl:7b
```

## Usage

Run the script by passing an image file as the argument:

```bash
python main.py /path/to/your/screenshot.png
```

### Example

```bash
python main.py ./examples/table.png
```

If successful, the script will create a CSV file in the current working directory.

## Supported input

The script is intended for image files containing tables, such as:

- `.png`
- `.jpg`
- `.jpeg`
- other image formats supported by your Ollama model setup

Best results usually come from:

- clean screenshots
- clear column headers
- minimal blur or compression
- tables with visible row and column separation

## Output behavior

- Output filename is based on the image filename
- The CSV file is written to the current working directory
- The model is instructed to return **raw CSV only**
- The script strips markdown CSV code fences if the model ignores instructions

## How it works

The extraction flow is simple:

- `ollama.chat()` sends the image and prompt to the selected local model
- the prompt asks for a strict 1:1 CSV representation of the table
- the response is cleaned with a regex to remove ```csv code fences
- the cleaned content is saved directly to a `.csv` file

## Notes and limitations

This is an AI-based extraction workflow, not a strict parser. That means:

- accuracy depends on image quality
- merged cells or unusual table layouts may not convert perfectly
- very dense or low-resolution tables may require manual cleanup afterward
- model choice matters a lot

For more reliable output, use:

- high-resolution screenshots
- cropped images containing only the table
- simple, well-structured tables

## Error handling

The script currently prints a basic error message if something fails, such as:

- Ollama not running
- the model not being installed
- invalid image path
- unsupported or unreadable file

## Known issue

The script's built-in usage message currently says:

```text
python main.py <screenshot.png>
```

But the actual uploaded filename is:

```text
main.py
```

## Project structure

```text
.
├── main.py
└── README.md
```
