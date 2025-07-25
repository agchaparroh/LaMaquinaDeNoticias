#!/usr/bin/env python3
"""
Extract and clean 'contenido_texto' field from JSON article files.

This script:
1. Reads JSON files from TEXTOS BRUTOS directory
2. Extracts the 'contenido_texto' field
3. Cleans and formats the text
4. Saves to Golden_DataSet/INPUT with format ART-XXXX.txt

No external dependencies required - uses only Python standard library.
"""

import glob
import json
import os
import random
import re
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_DIR = BASE_DIR / "TEXTOS BRUTOS"
OUTPUT_DIR = BASE_DIR / "Simplificación" / "Golden_DataSet" / "INPUT"


def clean_text(text):
    """
    Clean and format the extracted text.
    """
    if not text:
        return ""

    # Remove JavaScript code blocks
    text = re.sub(r"googletag\.cmd\.push\([^)]*\);?", "", text)
    text = re.sub(r"window\._taboola[^;]*;?", "", text)
    text = re.sub(r"_taboola\.push\([^)]*\);?", "", text)

    # Remove script tags and their content
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)

    # Remove HTML entities
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Remove URLs
    text = re.sub(r"https?://[^\s]+", "", text)

    # Remove email protection
    text = re.sub(r"/cdn-cgi/l/email-protection#[a-zA-Z0-9]+", "", text)

    # Fix spacing around punctuation
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    text = re.sub(r"([.,;:!?])(?=[A-Za-záéíóúñÁÉÍÓÚÑ])", r"\1 ", text)

    # Remove multiple spaces, tabs, and normalize whitespace
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r" +", " ", text)

    # Add paragraph breaks after periods followed by capital letters
    text = re.sub(r"\. ([A-ZÁÉÍÓÚÑ])", r".\n\n\1", text)

    # Clean up repeated newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove common artifacts
    patterns_to_remove = [
        r"Compartir en [A-Za-z]+",
        r"Compartir nota:",
        r"Temas Relacionados",
        r"Últimas Noticias",
        r"Contenido Patrocinado",
        r"julio \d+, 2025",
        r"Relacionadas",
        r"Ver biografía",
        r"Guardar",
        r'data-eio="l"',
        r"data-src=",
        r'decoding="async"',
        r'class="[^"]*"',
        r'alt="[^"]*"',
        r'title="[^"]*"',
        r'loading="lazy"',
        r"noscript>",
        r"<noscript>",
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Final cleanup of multiple spaces
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n ", "\n", text)
    text = re.sub(r" \n", "\n", text)

    return text.strip()


def generate_unique_id(existing_ids):
    """Generate a unique 4-digit ID."""
    while True:
        new_id = f"{random.randint(1000, 9999):04d}"
        if new_id not in existing_ids:
            return new_id


def main():
    """Main extraction process."""
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Track existing IDs to avoid duplicates
    existing_ids = set()
    existing_files = glob.glob(str(OUTPUT_DIR / "ART-*.txt"))
    for f in existing_files:
        match = re.search(r"ART-(\d{4})\.txt", f)
        if match:
            existing_ids.add(match.group(1))

    # Find all JSON files
    json_files = sorted(glob.glob(str(INPUT_DIR / "*.json")))

    if not json_files:
        print(f"No JSON files found in {INPUT_DIR}")
        return

    print(f"Found {len(json_files)} JSON files to process")

    # Mapping file to track conversions
    mapping_file = OUTPUT_DIR / "mapping.txt"

    processed = 0
    errors = 0

    with open(mapping_file, "w", encoding="utf-8") as mapping:
        mapping.write("# Mapping of JSON files to ART files\n")
        mapping.write("# Format: JSON_FILENAME -> ART-XXXX\n\n")

        for json_file in json_files:
            try:
                # Read JSON file
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Extract contenido_texto
                contenido_texto = data.get("contenido_texto", "")

                if not contenido_texto:
                    print(
                        f"WARNING: No contenido_texto in {os.path.basename(json_file)}"
                    )
                    continue

                # Clean the text
                cleaned_text = clean_text(contenido_texto)

                if not cleaned_text:
                    print(
                        f"WARNING: Empty text after cleaning for {os.path.basename(json_file)}"
                    )
                    continue

                # Generate unique ID
                art_id = generate_unique_id(existing_ids)
                existing_ids.add(art_id)

                # Save cleaned text
                output_file = OUTPUT_DIR / f"ART-{art_id}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)

                # Write mapping
                mapping.write(f"{os.path.basename(json_file)} -> ART-{art_id}\n")

                processed += 1
                print(f"Processed: {os.path.basename(json_file)} -> ART-{art_id}.txt")

            except Exception as e:
                errors += 1
                print(f"ERROR processing {os.path.basename(json_file)}: {e}")

    print(f"\n=== Summary ===")  # noqa: F541
    print(f"Total JSON files: {len(json_files)}")
    print(f"Successfully processed: {processed}")
    print(f"Errors: {errors}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Mapping file: {mapping_file}")


if __name__ == "__main__":
    main()
