"""
Unit tests for Task 3: Automated File Organizer (organizer.py)
Tests meet all Datheon safety and functionality requirements:
- Extension mapping (lowercase, uppercase, mixed-case)
- Unknown extensions untouched
- Existing destination folders
- Filename collision handling (safe renaming)
- Dry-run preview without filesystem modification
- Explicit cancellation safety
- Successful moves
- Invalid directory paths
- Directory safety (directories are never moved)
- Subdirectory non-recursion
- Uses Python temporary directories exclusively for safety
"""

from pathlib import Path
import tempfile
import unittest

import organizer


class TestOrganizerMappingAndSafety(unittest.TestCase):
    """Tests file extension classification and safety utilities."""

    def test_extension_mapping_categories(self):
        """Verify extension categorization for all standard categories."""
        self.assertEqual(organizer.get_category("document.pdf"), "Documents")
        self.assertEqual(organizer.get_category("report.docx"), "Documents")
        self.assertEqual(organizer.get_category("sheet.xlsx"), "Documents")
        self.assertEqual(organizer.get_category("photo.jpg"), "Images")
        self.assertEqual(organizer.get_category("graphic.PNG"), "Images")
        self.assertEqual(organizer.get_category("movie.mp4"), "Videos")
        self.assertEqual(organizer.get_category("archive.zip"), "Archives")
        self.assertEqual(organizer.get_category("script.py"), "Code")
        self.assertEqual(organizer.get_category("track.mp3"), "Audio")

    def test_case_insensitive_extension_matching(self):
        """Verify uppercase and mixed case extensions map to the correct category."""
        self.assertEqual(organizer.get_category("PHOTO.JPG"), "Images")
        self.assertEqual(organizer.get_category("doc.DOCX"), "Documents")
        self.assertEqual(organizer.get_category("clip.Mp4"), "Videos")
        self.assertEqual(organizer.get_category("BUNDLE.ZIP"), "Archives")

    def test_unknown_extension_untouched(self):
        """Verify unrecognized extensions return None."""
        self.assertIsNone(organizer.get_category("file.xyz"))
        self.assertIsNone(organizer.get_category("no_extension_file"))
        self.assertIsNone(organizer.get_category("binary.dat"))

    def test_filename_collision_handling(self):
        """Verify collision avoidance creates photo_1.jpg, photo_2.jpg, etc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir) / "Images"
            dest_dir.mkdir()

            # Create existing photo.jpg
            (dest_dir / "photo.jpg").write_text("existing", encoding="utf-8")

            # First collision should yield photo_1.jpg
            resolved = organizer.get_collision_free_destination(dest_dir, "photo.jpg")
            self.assertEqual(resolved.name, "photo_1.jpg")

            # Create photo_1.jpg as well
            (dest_dir / "photo_1.jpg").write_text("existing 1", encoding="utf-8")

            # Second collision should yield photo_2.jpg
            resolved2 = organizer.get_collision_free_destination(dest_dir, "photo.jpg")
            self.assertEqual(resolved2.name, "photo_2.jpg")


class TestOrganizerDryRunAndMoves(unittest.TestCase):
    """Tests scan planning, dry-run previews, confirmation, and execution."""

    def test_preview_makes_no_filesystem_changes(self):
        """Verify scan_and_plan_moves creates a plan without altering the filesystem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            f1 = base / "notes.txt"
            f2 = base / "pic.png"
            f1.write_text("notes", encoding="utf-8")
            f2.write_text("pic", encoding="utf-8")

            planned, skipped = organizer.scan_and_plan_moves(base)

            self.assertEqual(len(planned), 2)
            # Verify no folders were created
            self.assertFalse((base / "Documents").exists())
            self.assertFalse((base / "Images").exists())
            # Verify files are still in original root
            self.assertTrue(f1.exists())
            self.assertTrue(f2.exists())

    def test_directories_and_subfolders_are_not_moved(self):
        """Verify directories inside the folder are skipped and never moved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subfolder = base / "MyFolder"
            subfolder.mkdir()
            nested_file = subfolder / "inside.txt"
            nested_file.write_text("nested", encoding="utf-8")

            planned, skipped = organizer.scan_and_plan_moves(base)

            self.assertEqual(len(planned), 0)
            self.assertEqual(len(skipped), 1)
            self.assertEqual(skipped[0]["path"].resolve(), subfolder.resolve())
            self.assertEqual(skipped[0]["path"].name, "MyFolder")
            # Verify subfolder remains untouched
            self.assertTrue(subfolder.exists())
            self.assertTrue(nested_file.exists())

    def test_explicit_cancellation_safety(self):
        """Verify operation cancels cleanly and moves nothing if user does not type 'YES'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            test_file = base / "statement.pdf"
            test_file.write_text("content", encoding="utf-8")

            outputs = []
            inputs = ["NO"]  # Not "YES"

            def mock_input(prompt):
                return inputs.pop(0)

            def mock_print(*args, **kwargs):
                outputs.append(" ".join(str(a) for a in args))

            result = organizer.run_organizer(
                target_path=base,
                input_func=mock_input,
                print_func=mock_print
            )

            self.assertFalse(result)
            self.assertTrue(test_file.exists())
            self.assertFalse((base / "Documents").exists())
            combined = "\n".join(outputs)
            self.assertIn("CANCELLED", combined)

    def test_successful_organization(self):
        """Verify confirmed organization moves files to their appropriate category subfolders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            doc = base / "contract.pdf"
            img = base / "vacation.jpg"
            code = base / "script.py"
            unknown = base / "config.cfg"

            doc.write_text("pdf content", encoding="utf-8")
            img.write_text("jpg content", encoding="utf-8")
            code.write_text("print('hello')", encoding="utf-8")
            unknown.write_text("setting=1", encoding="utf-8")

            outputs = []
            inputs = ["YES"]

            def mock_input(prompt):
                return inputs.pop(0)

            def mock_print(*args, **kwargs):
                outputs.append(" ".join(str(a) for a in args))

            result = organizer.run_organizer(
                target_path=base,
                input_func=mock_input,
                print_func=mock_print
            )

            self.assertTrue(result)
            # Categorized files moved
            self.assertTrue((base / "Documents" / "contract.pdf").exists())
            self.assertTrue((base / "Images" / "vacation.jpg").exists())
            self.assertTrue((base / "Code" / "script.py").exists())
            # Unknown file untouched in root
            self.assertTrue((base / "config.cfg").exists())

    def test_invalid_directory_path_handling(self):
        """Verify error is reported when invalid path is given."""
        outputs = []

        def mock_print(*args, **kwargs):
            outputs.append(" ".join(str(a) for a in args))

        res = organizer.run_organizer(
            target_path="non_existent_folder_path_xyz_123",
            input_func=lambda p: "",
            print_func=mock_print
        )
        self.assertFalse(res)
        combined = "\n".join(outputs)
        self.assertIn("does not exist", combined)


if __name__ == "__main__":
    unittest.main()
