"""
Datheon Python Programming Internship - Task 3: Automated File Organizer

A safe, reliable command-line tool to organize cluttered folders:
- Validates the selected directory path.
- Categorizes common file types into Documents, Images, Videos, Archives, Code, and Audio.
- Case-insensitive extension mapping.
- Inspects only files directly inside the folder (non-recursive).
- Provides a detailed dry-run preview of planned moves before modifying anything.
- Requires explicit user confirmation ('YES') before performing any file move.
- Safe collision handling (e.g. photo_1.jpg) to prevent overwriting existing files.
- Protects directories and project script files from accidental moves.
- Never deletes files. Gracefully handles filesystem and permission errors.
"""

import os
from pathlib import Path
import shutil
import sys

# Categorization mapping (case-insensitive extensions to folder names)
CATEGORY_MAPPING = {
    # Documents
    ".pdf": "Documents",
    ".docx": "Documents",
    ".doc": "Documents",
    ".txt": "Documents",
    ".xlsx": "Documents",
    ".xls": "Documents",
    ".pptx": "Documents",
    ".csv": "Documents",
    ".odt": "Documents",
    ".rtf": "Documents",

    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".svg": "Images",
    ".webp": "Images",

    # Videos
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".mov": "Videos",
    ".avi": "Videos",
    ".flv": "Videos",
    ".wmv": "Videos",

    # Archives
    ".zip": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",

    # Code
    ".py": "Code",
    ".js": "Code",
    ".html": "Code",
    ".css": "Code",
    ".java": "Code",
    ".cpp": "Code",
    ".c": "Code",
    ".json": "Code",
    ".xml": "Code",
    ".sh": "Code",
    ".bat": "Code",

    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".ogg": "Audio",
}

# Files that should never be moved if the organizer is run in a project root
PROTECTED_FILENAMES = {
    "organizer.py",
    "hangman.py",
    "portfolio.py",
    "chatbot.py",
    "README.md",
    ".gitignore",
    "portfolio_summary.csv"
}


def get_category(filepath):
    """
    Returns the category name for a given file path based on its extension,
    or None if the extension is unknown.
    """
    suffix = Path(filepath).suffix.lower()
    return CATEGORY_MAPPING.get(suffix, None)


def get_collision_free_destination(destination_dir, filename, reserved_paths=None):
    """
    Determines a safe destination Path for a file to prevent overwriting.
    If 'report.pdf' exists, generates 'report_1.pdf', 'report_2.pdf', etc.
    Also respects any in-memory reserved paths from the current batch.
    """
    dest_folder = Path(destination_dir)
    original_path = dest_folder / filename
    reserved = reserved_paths if reserved_paths is not None else set()

    if not original_path.exists() and original_path not in reserved:
        return original_path

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1

    while True:
        candidate_name = f"{stem}_{counter}{suffix}"
        candidate_path = dest_folder / candidate_name
        if not candidate_path.exists() and candidate_path not in reserved:
            return candidate_path
        counter += 1


def scan_and_plan_moves(directory_path, protected_files=PROTECTED_FILENAMES):
    """
    Inspects files directly inside the given directory and creates a move plan.
    Does NOT recurse into subdirectories.
    Does NOT modify the filesystem.

    Returns:
      planned_moves: list of dicts describing planned operations
      skipped_items: list of dicts describing skipped files/directories
    """
    target = Path(directory_path).resolve()
    if not target.exists() or not target.is_dir():
        raise ValueError(f"Directory does not exist or is not a valid folder: {target}")

    planned_moves = []
    skipped_items = []
    reserved_destinations = set()

    for item in target.iterdir():
        # Avoid moving directories or symlinks pointing to directories
        if item.is_dir():
            skipped_items.append({
                "path": item,
                "reason": "Subdirectory (directories are not moved)"
            })
            continue

        # Skip protected script and configuration files
        if item.name in protected_files:
            skipped_items.append({
                "path": item,
                "reason": "Protected project file"
            })
            continue

        category = get_category(item)
        if category is None:
            skipped_items.append({
                "path": item,
                "reason": f"Unknown extension ({item.suffix or 'no extension'})"
            })
            continue

        dest_dir = target / category
        destination_path = get_collision_free_destination(
            dest_dir, item.name, reserved_paths=reserved_destinations
        )
        reserved_destinations.add(destination_path)

        is_renamed = destination_path.name != item.name

        planned_moves.append({
            "source": item,
            "category": category,
            "target_dir": dest_dir,
            "destination": destination_path,
            "is_renamed": is_renamed
        })

    return planned_moves, skipped_items


def format_preview_report(planned_moves, skipped_items):
    """
    Formats the planned moves and skipped files into a readable dry-run report.
    """
    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("              FILE ORGANIZER - DRY-RUN PREVIEW")
    lines.append("=" * 70)
    lines.append(f"Total planned moves : {len(planned_moves)}")
    lines.append(f"Total skipped items : {len(skipped_items)}")
    lines.append("-" * 70)

    if planned_moves:
        lines.append("\n[PLANNED FILE MOVES]:")
        for move in planned_moves:
            renamed_flag = f" [RENAMED to avoid collision -> {move['destination'].name}]" if move['is_renamed'] else ""
            lines.append(f"  - {move['source'].name}  -->  {move['category']}/{move['destination'].name}{renamed_flag}")
    else:
        lines.append("\nNo files qualify for organization.")

    if skipped_items:
        lines.append("\n[SKIPPED ITEMS (UNTOUCHED)]:")
        for skip in skipped_items:
            lines.append(f"  - {skip['path'].name} ({skip['reason']})")

    lines.append("=" * 70)
    return "\n".join(lines)


def execute_moves(planned_moves):
    """
    Safely executes the planned moves.
    Creates destination directories if necessary.
    Catches filesystem and permission errors per file.
    Returns: dict with 'moved' and 'failed' lists.
    """
    results = {
        "moved": [],
        "failed": []
    }

    for move in planned_moves:
        src = move["source"]
        target_dir = move["target_dir"]
        dst = move["destination"]

        try:
            # Create target category directory if not already created
            if not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)

            shutil.move(str(src), str(dst))
            results["moved"].append({
                "source": src,
                "destination": dst,
                "is_renamed": move["is_renamed"]
            })
        except (OSError, PermissionError, shutil.Error) as err:
            results["failed"].append({
                "source": src,
                "destination": dst,
                "error": str(err)
            })

    return results


def run_organizer(target_path=None, input_func=input, print_func=print):
    """
    Runs the complete interactive organizer workflow with user validation,
    dry-run preview, and explicit confirmation.
    """
    print_func("\n" + "=" * 60)
    print_func("         AUTOMATED FILE ORGANIZER (SAFETY FIRST)")
    print_func("=" * 60)
    print_func("This utility sorts files into categorized subfolders.")
    print_func("Safety Guarantee: A full preview is shown before moving anything,")
    print_func("and no files are ever deleted.\n")

    if target_path is None:
        try:
            raw_path = input_func("Enter the folder path to organize: ").strip()
        except (KeyboardInterrupt, EOFError):
            print_func("\nOperation cancelled by user.")
            return False
    else:
        raw_path = str(target_path)

    folder = Path(raw_path).expanduser().resolve()

    if not folder.exists():
        print_func(f"[!] Error: The folder '{folder}' does not exist.")
        return False

    if not folder.is_dir():
        print_func(f"[!] Error: '{folder}' is not a directory.")
        return False

    # Plan moves and generate dry-run preview
    try:
        planned_moves, skipped_items = scan_and_plan_moves(folder)
    except Exception as e:
        print_func(f"[!] Error inspecting folder: {e}")
        return False

    preview_text = format_preview_report(planned_moves, skipped_items)
    print_func(preview_text)

    if not planned_moves:
        print_func("\nNo files to move. Done.")
        return True

    # Explicit user confirmation check
    print_func("\n[SAFETY CONFIRMATION REQUIRED]")
    print_func("No changes have been made yet.")
    try:
        confirm = input_func("Type 'YES' to execute the planned moves (or anything else to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        print_func("\nOperation cancelled. No files were moved.")
        return False

    if confirm != "YES":
        print_func("\n[CANCELLED] Confirmation was not 'YES'. No files were moved or changed.")
        return False

    print_func("\nExecuting file moves...")
    results = execute_moves(planned_moves)

    print_func("\n" + "=" * 60)
    print_func("                 ORGANIZATION COMPLETED")
    print_func("=" * 60)
    print_func(f"Successfully moved : {len(results['moved'])} file(s)")
    print_func(f"Failed operations  : {len(results['failed'])} file(s)")
    print_func(f"Untouched items    : {len(skipped_items)} item(s)")

    if results["failed"]:
        print_func("\n[!] The following files could not be moved:")
        for fail in results["failed"]:
            print_func(f"  - {fail['source'].name} -> {fail['error']}")

    print_func("=" * 60 + "\n")
    return True


def main():
    """Main entry point."""
    run_organizer()


if __name__ == "__main__":
    main()
