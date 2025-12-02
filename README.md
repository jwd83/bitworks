# BitWorks

BitWorks is an open source educational game for learning Verilog (SystemVerilog) and assembly language fundamentals. Build digital logic from NAND gates up to working CPUs in a retro-styled development environment.

## Concept

Set in a make-believe world where our protagonist forms a rag-tag computer startup on an old 8-bit computer, players receive guidance and assignments via email from mentors and collaborate to build increasingly complex digital circuits.

## Features

### Retro IDE Interface
- **CRT-style display**: Green-on-black terminal aesthetic with smooth cursor fading
- **Multi-panel workspace**: File browser, email inbox, and Verilog editor
- **Fullscreen 16:9**: Scales to fit any display

### Integrated Development
- **File browser**: Navigate `.sv` (SystemVerilog) and `.s` (Assembly) files
- **Text editor**: Full editing with selection, clipboard, scrolling, and key repeat
- **Read-only protection**: Reference files (like `nand_gate.sv`) are protected; level files (like `1.sv`) are editable

### Educational Email System
- **Level-based progression**: Each level introduces new concepts
- **In-game documentation**: Reference materials, assignments, and hints delivered via email
- **Scrollable modal dialogs**: Read full email content with keyboard navigation

### Simulator Integration
- **PySVSim**: Companion SystemVerilog simulator in `..\pysvsim`
- **Verification**: Test your designs against expected truth tables
- **NAND gate counting**: Track design complexity

## Quick Start

```powershell
# Install dependencies
uv sync

# Run the game
uv run main.py
```

### Controls
- **Tab**: Cycle between panels (Files → Inbox → Editor)
- **F1**: File menu (New, Open, Save, Exit)
- **F2**: Edit menu (Cut, Copy, Paste)
- **F3**: Panel navigation menu
- **Arrow keys**: Navigate / move cursor
- **Shift+Arrows**: Select text
- **Ctrl+C/X/V**: Copy, Cut, Paste
- **Escape/Alt+F4**: Exit fullscreen

## Project Structure

```
bitworks/
├── main.py           # Game application (pygame-ce)
├── workspace/        # Player's Verilog files
│   ├── 1.sv          # Level 1 editable file (NOT gate)
│   ├── nand_gate.sv  # Reference NAND module (read-only)
│   └── *.sv          # Additional gate modules
├── emails/           # Level-based email content
│   └── 1/            # Level 1 emails
│       ├── 01_welcome.txt
│       ├── 02_reference.txt
│       └── ...
└── pyproject.toml    # Project configuration
```

## The J16 Architecture (Planned)

The J16 is a simple 16-bit Turing-complete processor with a single-cycle Harvard architecture. It's designed to complement books like "But How Do It Know?" by J. Clark Scott and encourage deeper learning about:

- Computer architecture fundamentals
- Digital logic design principles
- Assembly language programming (JASM)

## Related Projects

- **[PySVSim](../pysvsim)**: Pure Python SystemVerilog simulator used to verify player designs

## Dependencies

- Python 3.13+
- pygame-ce 2.5.5+
- uv (package manager)

## License

Open source - see LICENSE file.
