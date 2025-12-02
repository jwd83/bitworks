# AI Agent Instructions for BitWorks

This document provides context and guidelines for AI agents working on the BitWorks educational game.

## Project Overview

BitWorks is a retro-styled educational game where players learn digital logic design by writing SystemVerilog modules. The game integrates with **PySVSim** (`../pysvsim`) for simulation and verification.

## Key Files

- **main.py**: Complete pygame-ce application (~1500 lines)
- **workspace/**: Player-editable and reference SystemVerilog files
- **emails/**: Level-based educational content (email format)
- **pyproject.toml**: Project dependencies (pygame-ce)

## Architecture

### Application States

1. **Boot Sequence** (`boot_done = False`):
   - Simulates retro PC boot with timed text display
   - Skippable via Enter or Escape

2. **Workspace Mode** (`boot_done = True`):
   - Three-panel layout: File Browser, Email Inbox, Text Editor
   - Panel switching via Tab or F3 menu

### Key Global State Variables

```python
# Panels and navigation
active_panel = "editor"  # "editor", "files", "inbox"
selected_file_index = 0
selected_email_index = 0

# Text editing
text_buffer = [""]       # Document content as list of lines
cursor_x, cursor_y = 0, 0
editor_scroll_offset = 0

# Selection
selection_start_x, selection_start_y = None, None
selection_end_x, selection_end_y = None, None
selection_active = False
clipboard = ""

# File management
current_file = "1.sv"
file_read_only = False
current_level = 1
```

### Panel Layout

```
+------------------+--------------------------------+
|  File Browser    |                                |
|  (top-left 1/6)  |        Text Editor             |
+------------------+       (right 2/3)              |
|  Email Inbox     |                                |
|  (bottom-left)   |                                |
+------------------+--------------------------------+
|                    Status Bar                     |
+--------------------------------------------------+
```

### Read-Only File Detection

Files are editable or read-only based on their first character:
- **Editable**: Files starting with numbers (`1.sv`, `2.sv`, `33.s`)
- **Read-only**: Files starting with letters (`nand_gate.sv`, `not_gate.sv`)

```python
def is_file_read_only(filename):
    return not filename[0].isdigit()
```

## Key Functions

### Drawing
- `draw_boot_screen()`: Render boot sequence
- `draw_workspace()`: Main workspace with all panels
- `draw_file_browser()`: Left-top file list
- `draw_email_inbox()`: Left-bottom inbox with preview
- `draw_text_editor()`: Right-side code editor
- `draw_email_modal()`: Full-screen email viewer
- `draw_dropdown_menu()`: Menu overlays (drawn last for z-order)

### File Operations
- `scan_workspace_files()`: Find .sv and .s files
- `load_file_by_name(filename)`: Load file into editor
- `save_current_file()`: Save buffer to current file
- `is_file_read_only(filename)`: Check editability

### Email System
- `load_emails_for_level(level)`: Load emails from `emails/{level}/`
- `parse_email_file(path)`: Parse email header/content format
- `show_email_modal_dialog(index)`: Open email viewer

### Text Editing
- `handle_text_input(event)`: Main input processing
- `start_selection()`, `update_selection()`, `clear_selection()`: Selection management
- `copy_selection()`, `cut_selection()`, `paste_clipboard()`: Clipboard operations
- `ensure_cursor_visible()`: Auto-scroll to cursor

## Email File Format

```
From: sender@bitworks.edu
Date: 2025-10-11 08:00
Subject: Email Subject Line
Read: false

Email body content starts here after blank line.
Can be multiple paragraphs.
```

## Common Development Tasks

### Adding a New Level

1. Create `emails/{level}/` directory
2. Add numbered email files (e.g., `01_welcome.txt`, `02_reference.txt`)
3. Create level template file in workspace (e.g., `{level}.sv`)
4. Add reference modules as needed (read-only)

### Adding Menu Items

1. Add item to `menus` dictionary
2. Handle in `handle_menu_selection()`
3. Ensure F-key index mapping is correct

### Extending Editor Features

1. Add state variables at top of file
2. Modify `handle_text_input()` for keyboard handling
3. Update `draw_text_editor()` for visual changes
4. Test with selection and scrolling edge cases

## Integration with PySVSim

The simulator (`../pysvsim`) verifies player designs:

```powershell
# Test a player's module
python ../pysvsim/test_runner.py workspace/1.sv

# Generate truth table
python ../pysvsim/pysvsim.py --file workspace/1.sv
```

### Future Integration Points

- **Automatic verification**: Run pysvsim when player saves
- **Truth table display**: Show results in-game
- **NAND gate count**: Display complexity metric
- **Level completion**: Verify against expected outputs

## Visual Style Guidelines

- **Colors**: Black background, bright green text (`GREEN = (0, 255, 0)`)
- **Font**: Courier New (monospace), scaled to screen size
- **Menus**: Dark green background (`MENU_BG = (0, 60, 0)`)
- **Selection**: Medium green highlight (`SELECTION_BG = (0, 128, 0)`)
- **Effects**: Smooth sine-wave cursor fade for CRT aesthetic

## Known Issues / Limitations

- Single-file application (could benefit from modular refactor)
- No undo/redo system
- No syntax highlighting
- Simulator integration not yet automatic
- Only Level 1 content implemented

## Performance Notes

- Key repeat: 500ms delay, 75ms interval
- Boot sequence: 0.7s per line (skippable)
- Fullscreen at native 16:9 resolution
- Cursor fade: 1200ms cycle with glow effect
