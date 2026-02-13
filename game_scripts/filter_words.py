"""
Script to create words_small.txt from words.txt.
Filters words to include only those with less than 10 characters and no hyphens.
"""

from pathlib import Path


def filter_words(input_path: Path, output_path: Path) -> None:
    """
    Reads words from input_path and writes filtered words to output_path.
    Filters:
    - No punctuation (alphabetic characters only)
    - Length between 3 and 8 characters (inclusive)
    """
    with open(input_path, "r", encoding="utf-8") as f_in, open(
        output_path, "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            word = line.strip()
            if word.isalpha() and 3 <= len(word) <= 8:
                # Check for 3 consecutive identical letters
                has_triple = False
                for i in range(len(word) - 2):
                    if word[i].lower() == word[i + 1].lower() == word[i + 2].lower():
                        has_triple = True
                        break
                if not has_triple:
                    f_out.write(word + "\n")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_file = base_dir / "words.txt"
    output_file = base_dir / "words_small.txt"

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
    else:
        filter_words(input_file, output_file)
        print(f"Filtered words saved to {output_file}")
