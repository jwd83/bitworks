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

## Multi-Column Workspace Layout

### **Panel Structure**:
- **Left Third**: Split into File Browser (top) and Email Inbox (bottom)
- **Right Two-Thirds**: Text Editor for Verilog and Assembly files

### **File Browser Panel** (Top-Left):
- **File Types**: Shows .v (Verilog) and .s (Assembly) files from workspace folder
- **Navigation**: Arrow keys to select, Enter to open file, Tab to switch panels
- **Visual Indicators**: [V] for Verilog, [S] for Assembly, * for currently open file
- **Auto-scanning**: Automatically detects files in workspace directory

### **Email Inbox Panel** (Bottom-Left):
- **Two-Part Layout**: Email list (top half) and message preview (bottom half)
- **Status Indicators**: ● for unread emails, space for read emails
- **Message Preview**: Shows From, Date, Subject, and content preview
- **Full Message Modal**: Press Enter to view complete email in modal dialog
- **Navigation**: Arrow keys to select emails, Enter for full view
- **File-Based System**: Loads emails from `emails\{level}\` directory
- **Level-Based Learning**: Educational content organized by game levels

### **Text Editor Panel** (Right Two-Thirds):
- **Full-Featured Editor**: All text editing, selection, and clipboard capabilities
- **File Context**: Header shows currently open file name
- **Verilog-Focused**: Optimized for hardware description and assembly code

## Code Architecture

### Application Flow
The application follows a multi-panel workspace pattern:

1. **Boot Sequence Phase** (`boot_done = False`):
   - Simulates retro PC boot with timed text display
   - Shows BIOS messages, memory test, and DOS startup
   - Controlled by `boot_timer`, `boot_index`, and `boot_speed`

2. **Multi-Panel Workspace Phase** (`boot_done = True`):
   - Three-panel layout with file browser, inbox, and editor
   - Panel-aware navigation and context switching
   - Integrated file management and messaging system

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

## Text Selection and Clipboard

### **Selection Methods**:
- **Shift + Arrow Keys**: Hold Shift while using arrow keys to create text selections
- **Ctrl + A**: Select all text in the document

### **Clipboard Operations**:
- **Copy**: Ctrl + C or F2 → F2 (Copy menu)
- **Cut**: Ctrl + X or F2 → F1 (Cut menu)
- **Paste**: Ctrl + V or F2 → F3 (Paste menu)

### **Selection Features**:
- **Visual Highlighting**: Selected text is highlighted with darker green background
- **Multi-line Selection**: Supports text selection across multiple lines
- **Smart Deletion**: Typing or pressing Delete/Backspace replaces selected text
- **Auto-clear**: Selection clears when cursor moves without Shift pressed

### **Enhanced Navigation**:
- **Home/End Keys**: Jump to beginning/end of current line
- **Delete Key**: Delete character after cursor or selected text
- **Extended Arrow Movement**: Arrow keys can move between lines at boundaries

## Key Repeat System

- **Initial Delay**: 750ms (3/4 second) before key starts repeating
- **Repeat Rate**: 250ms (1/4 second) between repeat events
- **Smart Filtering**: Only navigation and text editing keys repeat (not function keys)
- **Supported Keys**: Arrow keys, Backspace, Delete, Home, End, and printable characters

## Level-Based Learning System

### **Level 1 Objectives**: 
- **Goal**: Create a NOT gate (inverter) using the provided NAND gate module
- **Key Skills**: Module instantiation, port connections, digital logic understanding
- **Resources**: 5 instructional emails covering theory, reference, assignment, hints, and advanced concepts
- **Files**: `nand.v` (provided component), `not_template.v` (student template)
- **Challenge**: Understanding that NAND(a,a) = NOT(a)

### **Email Learning System**:
- **Welcome Email**: Course introduction and level overview
- **Reference Documentation**: Complete NAND module interface and usage examples  
- **Assignment Specification**: Detailed requirements and grading criteria
- **Implementation Hints**: Step-by-step guidance and common mistakes
- **Advanced Concepts**: Theory background and real-world connections

### **Game Progression**:
- **File-Based Content**: Emails loaded from `emails\{level}\` directory structure
- **Scalable Design**: Easy to add new levels by creating new email folders
- **Educational Focus**: Each level teaches specific digital design concepts
- **Practical Application**: Real Verilog code development with immediate feedback

## Technical Notes

- The application uses pygame-ce (Community Edition) rather than standard pygame for better maintained libraries and additional features
- Boot sequence timing can be adjusted via `boot_speed` variable
- Text editor supports unlimited document length (limited only by memory)
- Cursor blinking is implemented with a timer-based visibility toggle
- Text selection uses coordinate-based highlighting for precise visual feedback
- Clipboard operations work with both single-line and multi-line text
- Email system dynamically loads content from structured file directories
- Level progression system supports expandable educational content
