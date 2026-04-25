import argparse
import logging
import re
import sys
from pathlib import Path

import ollama


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
DEFAULT_MODEL = "qwen2.5vl:7b"

PROMPT = (
    "Extract the table from this image into a 1:1 CSV format. "
    "Use commas as delimiters. "
    "Preserve the exact column headers and row data. "
    "Return ONLY the raw CSV content with no markdown, code fences, or explanation."
)


def extract_csv_from_image(image_path: str, model: str, output_dir: Path) -> bool:
    """Extract table data from an image and save it as a CSV file. Returns True on success."""
    path = Path(image_path)

    if not path.exists():
        logging.error("File not found: %s", image_path)
        return False

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logging.warning(
            "Unrecognized extension '%s' for %s — attempting anyway",
            path.suffix,
            path.name,
        )

    logging.info("Processing %s with %s", path.name, model)

    try:
        response = ollama.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": PROMPT,
                "images": [image_path],
            }],
            options={"temperature": 0},
        )

        raw_content = response["message"]["content"]
        logging.debug("Raw model response:\n%s", raw_content)

        csv_data = re.sub(r"```csv\n|```", "", raw_content).strip()

        output_file = output_dir / (path.stem + ".csv")
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

    return False


def main():
    """Parse arguments and process image files."""
    parser = argparse.ArgumentParser(
        description="Extract table data from images and save as CSV using a local Ollama vision model."
    )
    parser.add_argument("images", nargs="+", help="Image file(s) to process")
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
    if not output_dir.is_dir():
        logging.error("Output directory does not exist: %s", output_dir)
        sys.exit(1)

    total = len(args.images)
    results = []
    for i, image in enumerate(args.images, start=1):
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
