# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Bitworks is a retro-style text editor simulation built with pygame-ce. The application simulates a classic PC boot sequence followed by a functional text editor with a retro green-on-black terminal aesthetic.

## Development Environment

- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: uv (modern, fast Python package manager)
- **Main Dependency**: pygame-ce (Community Edition of pygame)
- **Project Structure**: Single-file application (`main.py`)

## Common Commands

### Environment Setup
```powershell
# Install dependencies
uv sync

# Activate virtual environment (if needed)
.venv\Scripts\Activate.ps1
```

### Running the Application
```powershell
# Run the main application
uv run main.py

# Or with Python directly (if venv is activated)
python main.py
```

### Development Commands
```powershell
# Add new dependencies
uv add <package-name>

# Update dependencies
uv sync --upgrade

# Show dependency tree
uv tree

# Run Python REPL with project dependencies
uv run python
```

## Code Architecture

### Application Flow
The application follows a simple state machine pattern:

1. **Boot Sequence Phase** (`boot_done = False`):
   - Simulates retro PC boot with timed text display
   - Shows BIOS messages, memory test, and DOS startup
   - Controlled by `boot_timer`, `boot_index`, and `boot_speed`

2. **Text Editor Phase** (`boot_done = True`):
   - Functional text editor with cursor navigation
   - Menu system activated by function keys (F1-F3)
   - Text buffer stored as list of strings

### Key Components

**Display System**:
- `draw_boot_screen()`: Renders boot sequence
- `draw_editor()`: Renders text editor interface with menu bar
- Screen resolution: 800x600 pixels
- Font: Courier New, simulating monospace terminal text

**Text Editing Engine**:
- `text_buffer`: List of strings representing document lines
- `cursor_x`, `cursor_y`: Current cursor position
- `handle_text_input()`: Processes keyboard input for text manipulation
- Supports basic text operations: typing, backspace, enter, cursor movement

**Menu System**:
- `active_menu`: Tracks which function key menu is open
- `menus` dictionary: Maps F1-F3 to menu items (File, Edit, Help)
- Menus are visual overlays but not yet functionally implemented

### Color Scheme
- Background: Black (`BLACK = (0, 0, 0)`)
- Text: Bright Green (`GREEN = (0, 255, 0)`)
- Menu Background: Dark Green (`MENU_BG = (0, 60, 0)`)
- UI Elements: Gray (`GRAY = (50, 50, 50)`)

## Development Patterns

When extending this codebase:

1. **State Management**: The application uses global variables for state. Consider refactoring to a class-based approach for complex features.

2. **Event Handling**: All input is processed in the main game loop. New input types should be added to the event handling section.

3. **Rendering**: Separate draw functions maintain clean separation between game state and display logic.

4. **Retro Aesthetic**: Maintain the green-on-black color scheme and use monospace fonts to preserve the retro terminal feel.

## Project File Structure

- `main.py`: Complete application in a single file
- `pyproject.toml`: Project metadata and dependencies
- `uv.lock`: Locked dependency versions for reproducible builds
- `.python-version`: Python version specification for consistency
- `.venv/`: Virtual environment (auto-created by uv)

## Technical Notes

- The application uses pygame-ce (Community Edition) rather than standard pygame for better maintained libraries and additional features
- Boot sequence timing can be adjusted via `boot_speed` variable
- Text editor supports unlimited document length (limited only by memory)
- Cursor blinking is implemented with a timer-based visibility toggle