"""Extract table data from images and save as CSV using a local Ollama vision model."""
import argparse
import csv
import io
import logging
import re
import sys
from pathlib import Path

import ollama


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
# Instruct variant avoids thinking traces that pollute CSV (think=false is ignored on qwen3-vl).
DEFAULT_MODEL = "qwen3-vl:8b-instruct"

PROMPT = (
    "Extract the table from this image into a 1:1 CSV format. "
    "Use commas as delimiters. "
    "If a cell contains a comma, newline, or double quote, wrap it in double quotes "
    "and escape internal quotes by doubling them. "
    "Preserve the exact column headers and row data. "
    "Return ONLY the raw CSV content with no markdown, code fences, or explanation."
)

FENCE_RE = re.compile(r"```(?:csv)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def extract_csv_text(raw_content: str) -> str:
    """Strip thinking traces and markdown fences; return the CSV payload."""
    text = THINK_RE.sub("", raw_content or "").strip().lstrip("\ufeff")
    fenced = FENCE_RE.findall(text)
    if fenced:
        text = max(fenced, key=len).strip()
    return text


def csv_looks_valid(text: str) -> bool:
    """Return True if the text parses as CSV with at least one non-empty row."""
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return False
    return any(any(cell.strip() for cell in row) for row in rows)


def extract_csv_from_image(image_path: str, model: str, output_dir: Path) -> bool:
    """Extract table data from an image and save it as a CSV file. Returns True on success."""
    path = Path(image_path)

    if not path.exists():
        logging.error("File not found: %s", image_path)
        return False

    if not path.is_file():
        logging.error("Not a file: %s", image_path)
        return False

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logging.warning(
            "Unrecognized extension '%s' for %s — attempting anyway",
            path.suffix,
            path.name,
        )

    logging.info("Processing %s with %s", path.name, model)

    try:
        chat_kwargs = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": PROMPT,
                "images": [str(path.resolve())],
            }],
            "options": {"temperature": 0},
        }
        try:
            response = ollama.chat(**chat_kwargs, think=False)
        except TypeError:
            response = ollama.chat(**chat_kwargs)

        raw_content = response["message"].get("content") or ""
        logging.debug("Raw model response:\n%s", raw_content)

        csv_data = extract_csv_text(raw_content)
        if not csv_data:
            logging.error("Empty CSV extracted from %s", path.name)
            return False
        if not csv_looks_valid(csv_data):
            logging.warning(
                "Output from %s may not be valid CSV; saving anyway",
                path.name,
            )

        output_file = output_dir / (path.stem + ".csv")
        if output_file.exists():
            logging.warning("Overwriting existing file: %s", output_file)
        output_file.write_text(csv_data, encoding="utf-8")
        logging.info("Saved: %s", output_file)
        return True

    except ollama.ResponseError as e:
        logging.error("Ollama error for %s: %s", path.name, e)
        logging.error(
            "Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull %s`)",
            model,
        )
    except (KeyError, TypeError) as e:
        logging.error("Unexpected response format for %s: %s", path.name, e)
    except OSError as e:
        logging.error("File I/O error for %s: %s", path.name, e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Failed to call Ollama for %s: %s", path.name, e)
        logging.error(
            "Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull %s`)",
            model,
        )

    return False


def collect_images(inputs: list[str]) -> list[str]:
    """Expand directories into supported image files; keep explicit file paths as-is."""
    collected: list[str] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            matches = sorted(
                p for p in path.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            if not matches:
                logging.warning("No supported images found in directory: %s", path)
            collected.extend(str(p) for p in matches)
        else:
            collected.append(item)
    return collected


def main() -> None:
    """Parse arguments and process image files."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract table data from images and save as CSV "
            "using a local Ollama vision model."
        )
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Image file(s) or directories of images to process",
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Directory for output CSV files (default: current directory)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verbose", "-v", action="store_true", help="Enable debug output")
    group.add_argument("--quiet", "-q", action="store_true", help="Suppress info messages")
    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    output_dir = Path(args.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error("Cannot create output directory %s: %s", output_dir, e)
        sys.exit(1)

    images = collect_images(args.images)
    if not images:
        logging.error("No images to process.")
        sys.exit(1)

    total = len(images)
    results = []
    for i, image in enumerate(images, start=1):
        if total > 1:
            logging.info("Processing file %d/%d", i, total)
        results.append(extract_csv_from_image(image, args.model, output_dir))

    success = sum(results)
    if total > 1:
        logging.info("Processed %d/%d files successfully.", success, total)

    if success < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
