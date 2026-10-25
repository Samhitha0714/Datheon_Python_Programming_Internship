"""
Datheon Python Programming Internship - Task 1: Hangman Word Guessing Game

A clean, modular terminal-based Hangman game adhering strictly to all Datheon requirements:
- Works completely offline with a built-in English word bank.
- Allows exactly 6 incorrect guesses before defeat.
- 7 progressively updated ASCII gallows stages (0 to 6 incorrect guesses).
- Validates single alphabetic character input and prevents duplicate guess penalties.
- Supports graceful exit using 'QUIT'.
"""

import random
import sys

# Built-in offline word list for the game
DEFAULT_WORDS = [
    "PYTHON", "DEVELOPER", "ALGORITHM", "VARIABLE", "FUNCTION",
    "COMPUTER", "KEYBOARD", "DATABASE", "SOFTWARE", "NETWORK",
    "TERMINAL", "PROJECT", "STUDENT", "LOGIC", "PROGRAMMING",
    "STRUCTURE", "DEBUGGER", "LOOP", "INTEGER", "BOOLEAN"
]

MAX_INCORRECT_GUESSES = 6

# ASCII Gallows Art: Stage 0 (empty) through Stage 6 (full body / defeat)
GALLOWS_STAGES = [
    """
  +---+
  |   |
      |
      |
      |
      |
=========""",
    """
  +---+
  |   |
  O   |
      |
      |
      |
=========""",
    """
  +---+
  |   |
  O   |
  |   |
      |
      |
=========""",
    """
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========""",
    """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========""",
    """
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=========""",
    """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
========="""
]


from pathlib import Path

DEFAULT_WORDS_FILE = Path("sample_data") / "hangman_words.txt"


def load_word_list(words_file=DEFAULT_WORDS_FILE):
    """
    Loads English words from a local file, returning a list of uppercase words.
    Falls back to DEFAULT_WORDS if the file is missing or empty.
    """
    path = Path(words_file)
    if path.exists() and path.is_file():
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                words = [line.strip().upper() for line in f if len(line.strip()) >= 3 and line.strip().isalpha()]
                if words:
                    return words
        except OSError:
            pass
    return DEFAULT_WORDS


def choose_word(word_list=None, words_file=DEFAULT_WORDS_FILE):
    """
    Selects a random uppercase word from the provided word list, local words file, or default list.
    """
    if word_list is not None:
        if not word_list:
            raise ValueError("Word list cannot be empty.")
        pool = word_list
    else:
        pool = load_word_list(words_file)

    if not pool:
        raise ValueError("Word list cannot be empty.")
    return random.choice(pool).strip().upper()


def get_masked_word(secret_word, guessed_letters):
    """
    Returns the secret word masked with underscores for unrevealed letters,
    with spaces between characters for visual clarity.
    Example: 'P _ T H _ N'
    """
    masked = [letter if letter in guessed_letters else "_" for letter in secret_word]
    return " ".join(masked)


def is_word_guessed(secret_word, guessed_letters):
    """
    Checks if all unique letters of the secret word have been guessed.
    """
    return set(secret_word).issubset(set(guessed_letters))


def get_stage_art(incorrect_count):
    """
    Returns the ASCII art stage corresponding to the number of incorrect guesses.
    Clamps between 0 and MAX_INCORRECT_GUESSES.
    """
    clamped_index = max(0, min(incorrect_count, MAX_INCORRECT_GUESSES))
    return GALLOWS_STAGES[clamped_index]


def validate_guess(raw_input):
    """
    Validates user input.
    Accepts 'QUIT' (case-insensitive) or a single alphabetic letter.
    Returns: (is_valid: bool, cleaned_value: str, error_message: str)
    """
    if raw_input is None:
        return False, "", "Input cannot be empty. Please enter a letter or 'QUIT'."

    cleaned = raw_input.strip()

    if not cleaned:
        return False, "", "Empty input. Please enter a single letter (A-Z) or 'QUIT' to exit."

    if cleaned.upper() == "QUIT":
        return True, "QUIT", ""

    if len(cleaned) == 1 and cleaned.isalpha():
        return True, cleaned.upper(), ""

    return False, "", f"Invalid input '{cleaned}'. Please enter exactly one letter (A-Z) or 'QUIT'."


def process_guess(guess, secret_word, guessed_letters, incorrect_count):
    """
    Processes a validated single-letter guess.
    Updates guessed_letters in-place (set).
    Returns: (status: str, new_incorrect_count: int, feedback_message: str)
    Status can be: 'DUPLICATE', 'CORRECT', or 'INCORRECT'.
    """
    letter = guess.upper()

    if letter in guessed_letters:
        return (
            "DUPLICATE",
            incorrect_count,
            f"You already guessed '{letter}'. No attempt deducted."
        )

    guessed_letters.add(letter)

    if letter in secret_word:
        return (
            "CORRECT",
            incorrect_count,
            f"Good guess! Letter '{letter}' is in the secret word."
        )
    else:
        new_count = incorrect_count + 1
        return (
            "INCORRECT",
            new_count,
            f"Sorry, letter '{letter}' is NOT in the secret word."
        )


def play_game(secret_word=None, input_func=input, print_func=print):
    """
    Runs an interactive or test-driven game of Hangman.
    Returns: 'WIN', 'LOSS', or 'QUIT'
    """
    if secret_word is None:
        secret_word = choose_word()
    else:
        secret_word = secret_word.strip().upper()

    guessed_letters = set()
    incorrect_count = 0

    print_func("\n" + "=" * 45)
    print_func("     WELCOME TO HANGMAN WORD GUESSING GAME")
    print_func("=" * 45)
    print_func("Rules: Guess the secret word one letter at a time.")
    print_func(f"You have a maximum of {MAX_INCORRECT_GUESSES} incorrect guesses.")
    print_func("Type 'QUIT' at any prompt to exit the game.\n")

    while incorrect_count < MAX_INCORRECT_GUESSES:
        # Display current visual state
        print_func(get_stage_art(incorrect_count))
        print_func(f"\nWord: {get_masked_word(secret_word, guessed_letters)}")
        remaining = MAX_INCORRECT_GUESSES - incorrect_count
        print_func(f"Remaining incorrect attempts: {remaining} of {MAX_INCORRECT_GUESSES}")

        guessed_list = sorted(list(guessed_letters))
        guessed_display = ", ".join(guessed_list) if guessed_list else "None"
        print_func(f"Guessed letters so far: {guessed_display}")

        # Prompt for user guess
        try:
            raw_guess = input_func("Enter your guess (or 'QUIT' to exit): ")
        except (KeyboardInterrupt, EOFError):
            print_func("\nGame interrupted. Exiting gracefully.")
            return "QUIT"

        is_valid, cleaned, error_msg = validate_guess(raw_guess)
        if not is_valid:
            print_func(f"[!] {error_msg}")
            continue

        if cleaned == "QUIT":
            print_func("\nYou chose to quit the game.")
            print_func(f"The secret word was: {secret_word}")
            print_func("Thank you for playing Hangman!\n")
            return "QUIT"

        status, incorrect_count, message = process_guess(
            cleaned, secret_word, guessed_letters, incorrect_count
        )
        print_func(f"[i] {message}")

        # Check for victory condition
        if is_word_guessed(secret_word, guessed_letters):
            print_func(get_stage_art(incorrect_count))
            print_func("\n" + "*" * 45)
            print_func("  CONGRATULATIONS! YOU WON THE GAME!")
            print_func(f"  Secret Word: {secret_word}")
            print_func(f"  Incorrect Guesses: {incorrect_count} / {MAX_INCORRECT_GUESSES}")
            print_func("*" * 45 + "\n")
            return "WIN"

    # Defeat condition reached after 6 incorrect guesses
    print_func(get_stage_art(incorrect_count))
    print_func("\n" + "-" * 45)
    print_func("  GAME OVER! YOU HAVE BEEN HANGED.")
    print_func(f"  The secret word was: {secret_word}")
    print_func("  Better luck next time!")
    print_func("-" * 45 + "\n")
    return "LOSS"


def main():
    """Main entry point for running the Hangman game."""
    play_game()


if __name__ == "__main__":
    main()
