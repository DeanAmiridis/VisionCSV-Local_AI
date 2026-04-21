import ollama
import sys
import re
from pathlib import Path


def extract_csv_from_image(image_path):
    MODEL = "qwen2.5vl:7b"
    
    print(f"--- Processing {image_path} with {MODEL} ---")

    prompt = """
    Extract the table from this image into a 1:1 CSV format.
    - Use commas as delimiters.
    - Preserving the exact column headers and row data.
    - Return ONLY the raw CSV content.
    - Don't include any conversational text, md code blocks, or explanations.
    """

    try:
        response = ollama.chat(
            model=MODEL,
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
        with open(output_file, "w") as f:
            f.write(csv_data)
        print(f"Done! File saved as: {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ollama_to_csv.py <screenshot.png>")
    else:
        extract_csv_from_image(sys.argv[1])
