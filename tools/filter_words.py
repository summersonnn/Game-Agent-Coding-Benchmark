"""
Regenerates game_scripts/words_small.txt from game_scripts/words.txt.
Filters to 3-8 character alphabetic words with no triple-identical consecutive letters.
Run this if words_small.txt is missing or corrupted.
"""

from pathlib import Path


def filter_words(input_path: Path, output_path: Path) -> None:
    """
    Reads words from input_path and writes filtered words to output_path.
    Filters:
    - No punctuation (alphabetic characters only)
    - Length between 3 and 8 characters (inclusive)
    - No three consecutive identical letters
    """
    with open(input_path, "r", encoding="utf-8") as f_in, open(
        output_path, "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            word = line.strip()
            if word.isalpha() and 3 <= len(word) <= 8:
                has_triple = False
                for i in range(len(word) - 2):
                    if word[i].lower() == word[i + 1].lower() == word[i + 2].lower():
                        has_triple = True
                        break
                if not has_triple:
                    f_out.write(word + "\n")


if __name__ == "__main__":
    game_scripts_dir = Path(__file__).parent.parent / "game_scripts"
    input_file = game_scripts_dir / "words.txt"
    output_file = game_scripts_dir / "words_small.txt"

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
    else:
        filter_words(input_file, output_file)
        print(f"Filtered words saved to {output_file}")
