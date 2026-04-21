"""Extract CSV tables from images using a local Ollama vision model."""

import sys
import re
from pathlib import Path

import ollama


MODEL_NAME = "qwen2.5vl:7b"


def extract_csv_from_image(image_path):
    """Extract table data from an image and save it as a CSV file."""
    print(f"--- Processing {image_path} with {MODEL_NAME} ---")

    prompt = """
    Extract the table from this image into a 1:1 CSV format.
    - Use commas as delimiters.
    - Preserving the exact column headers and row data.
    - Return ONLY the raw CSV content.
    - Don't include any conversational text, md code blocks, or explanations.
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }],
            options={'temperature': 0}
        )

        raw_content = response['message']['content']

        # Clean-up
        csv_data = re.sub(r'```csv\n|```', '', raw_content).strip()

        output_file = Path(image_path).stem + ".csv"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(csv_data)
        print(f"Done! File saved as: {output_file}")

    except (KeyError, TypeError, OSError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <screenshot.png>")
    else:
        extract_csv_from_image(sys.argv[1])
