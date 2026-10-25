"""
Unit tests for Task 1: Hangman Word Guessing Game (hangman.py)
Tests meet all Datheon requirements:
- Word masking
- Correct guesses
- Incorrect guesses
- Repeated letters in the secret word
- Duplicate correct and incorrect guesses
- Input validation
- Drawing-stage progression
- Victory, defeat, and quit states
"""

import unittest
from unittest.mock import patch
import hangman


class TestHangmanLogic(unittest.TestCase):
    """Tests core Hangman logic independent of user input."""

    def test_choose_word_default(self):
        """Verify choose_word returns an uppercase string from default list."""
        word = hangman.choose_word()
        self.assertIsInstance(word, str)
        self.assertIn(word, hangman.load_word_list())
        self.assertTrue(word.isupper())

    def test_choose_word_custom_list(self):
        """Verify choose_word works with a provided custom list."""
        custom_list = ["TESTING", "PYTHON"]
        word = hangman.choose_word(custom_list)
        self.assertIn(word, ["TESTING", "PYTHON"])

    def test_choose_word_empty_list_raises_error(self):
        """Verify choose_word raises ValueError when pool is empty."""
        with self.assertRaises(ValueError):
            hangman.choose_word([])

    def test_word_masking_initial(self):
        """Verify that with no guesses, word shows all underscores."""
        secret = "PYTHON"
        guessed = set()
        masked = hangman.get_masked_word(secret, guessed)
        self.assertEqual(masked, "_ _ _ _ _ _")

    def test_word_masking_partial_and_repeated_letters(self):
        """Verify that repeated letters are masked and revealed properly."""
        secret = "BANANA"
        guessed = {"A"}
        masked = hangman.get_masked_word(secret, guessed)
        self.assertEqual(masked, "_ A _ A _ A")

        guessed.add("N")
        masked2 = hangman.get_masked_word(secret, guessed)
        self.assertEqual(masked2, "_ A N A N A")

    def test_is_word_guessed(self):
        """Verify win condition detection."""
        secret = "APPLE"
        self.assertFalse(hangman.is_word_guessed(secret, {"A", "P"}))
        self.assertTrue(hangman.is_word_guessed(secret, {"A", "P", "L", "E"}))
        # Extra letters guessed should still count as guessed
        self.assertTrue(hangman.is_word_guessed(secret, {"A", "P", "L", "E", "Z", "X"}))

    def test_validate_guess_valid_letters(self):
        """Verify valid single letters are accepted and uppercased."""
        valid, val, msg = hangman.validate_guess("a")
        self.assertTrue(valid)
        self.assertEqual(val, "A")
        self.assertEqual(msg, "")

        valid, val, msg = hangman.validate_guess(" Z ")
        self.assertTrue(valid)
        self.assertEqual(val, "Z")

    def test_validate_guess_quit(self):
        """Verify QUIT is recognized case-insensitively."""
        for q in ["quit", "QUIT", "Quit", "  quit  "]:
            valid, val, msg = hangman.validate_guess(q)
            self.assertTrue(valid)
            self.assertEqual(val, "QUIT")

    def test_validate_guess_invalid_inputs(self):
        """Verify multi-character, non-alpha, empty, and None inputs are rejected."""
        invalid_cases = ["", "   ", None, "1", "ab", "!", "hello", "123"]
        for case in invalid_cases:
            valid, val, msg = hangman.validate_guess(case)
            self.assertFalse(valid, f"Should reject invalid input: {case!r}")
            self.assertTrue(len(msg) > 0)

    def test_process_guess_correct(self):
        """Verify correct guess updates guessed_letters without increasing count."""
        secret = "PYTHON"
        guessed = set()
        status, count, msg = hangman.process_guess("P", secret, guessed, 0)
        self.assertEqual(status, "CORRECT")
        self.assertEqual(count, 0)
        self.assertIn("P", guessed)

    def test_process_guess_incorrect(self):
        """Verify incorrect guess increments count and updates guessed_letters."""
        secret = "PYTHON"
        guessed = set()
        status, count, msg = hangman.process_guess("Z", secret, guessed, 0)
        self.assertEqual(status, "INCORRECT")
        self.assertEqual(count, 1)
        self.assertIn("Z", guessed)

    def test_process_guess_duplicate_correct(self):
        """Verify duplicate correct guess does NOT increment count."""
        secret = "PYTHON"
        guessed = {"P"}
        status, count, msg = hangman.process_guess("P", secret, guessed, 0)
        self.assertEqual(status, "DUPLICATE")
        self.assertEqual(count, 0)

    def test_process_guess_duplicate_incorrect(self):
        """Verify duplicate incorrect guess does NOT penalize with extra mistake."""
        secret = "PYTHON"
        guessed = {"Z"}
        status, count, msg = hangman.process_guess("Z", secret, guessed, 2)
        self.assertEqual(status, "DUPLICATE")
        self.assertEqual(count, 2)

    def test_drawing_stage_progression(self):
        """Verify drawing stage progression from 0 to 6."""
        self.assertEqual(len(hangman.GALLOWS_STAGES), 7)
        for i in range(7):
            stage = hangman.get_stage_art(i)
            self.assertEqual(stage, hangman.GALLOWS_STAGES[i])

        # Clamping checks
        self.assertEqual(hangman.get_stage_art(-1), hangman.GALLOWS_STAGES[0])
        self.assertEqual(hangman.get_stage_art(10), hangman.GALLOWS_STAGES[6])


class TestHangmanGameFlow(unittest.TestCase):
    """Tests complete game flows using mocked inputs and outputs."""

    def test_game_flow_victory(self):
        """Simulate a winning game for secret word 'CAT'."""
        inputs = ["c", "a", "t"]
        output_lines = []

        def mock_input(prompt):
            return inputs.pop(0)

        def mock_print(*args, **kwargs):
            output_lines.append(" ".join(str(a) for a in args))

        result = hangman.play_game(secret_word="CAT", input_func=mock_input, print_func=mock_print)
        self.assertEqual(result, "WIN")
        combined_output = "\n".join(output_lines)
        self.assertIn("CONGRATULATIONS", combined_output)

    def test_game_flow_defeat_after_six_mistakes(self):
        """Simulate exactly 6 mistakes leading to defeat."""
        # 'CAT' -> incorrect guesses: B, D, E, F, G, H (6 incorrect)
        inputs = ["b", "d", "e", "f", "g", "h"]
        output_lines = []

        def mock_input(prompt):
            return inputs.pop(0)

        def mock_print(*args, **kwargs):
            output_lines.append(" ".join(str(a) for a in args))

        result = hangman.play_game(secret_word="CAT", input_func=mock_input, print_func=mock_print)
        self.assertEqual(result, "LOSS")
        combined_output = "\n".join(output_lines)
        self.assertIn("GAME OVER", combined_output)
        self.assertIn("The secret word was: CAT", combined_output)

    def test_game_flow_quit(self):
        """Simulate player quitting midway through the game."""
        inputs = ["a", "quit"]
        output_lines = []

        def mock_input(prompt):
            return inputs.pop(0)

        def mock_print(*args, **kwargs):
            output_lines.append(" ".join(str(a) for a in args))

        result = hangman.play_game(secret_word="PYTHON", input_func=mock_input, print_func=mock_print)
        self.assertEqual(result, "QUIT")
        combined_output = "\n".join(output_lines)
        self.assertIn("You chose to quit the game", combined_output)

    def test_game_flow_with_invalid_and_duplicate_inputs(self):
        """Verify invalid inputs and duplicate guesses don't cause defeat early."""
        # secret word: 'GO'
        # inputs: empty, number, 'g', 'g' (duplicate), 'x' (incorrect 1), 'x' (duplicate incorrect), 'o' (win)
        inputs = ["", "12", "g", "g", "x", "x", "o"]
        output_lines = []

        def mock_input(prompt):
            return inputs.pop(0)

        def mock_print(*args, **kwargs):
            output_lines.append(" ".join(str(a) for a in args))

        result = hangman.play_game(secret_word="GO", input_func=mock_input, print_func=mock_print)
        self.assertEqual(result, "WIN")


if __name__ == "__main__":
    unittest.main()
