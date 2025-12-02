# BitWorks Project Summary

## Current State (December 2025)

BitWorks is a functional retro-styled IDE game for learning digital logic design through SystemVerilog. The core game loop is playable for Level 1.

### Completed Features

**User Interface**
- Fullscreen 16:9 display with dynamic font scaling
- Retro CRT aesthetic (green-on-black, smooth cursor fade with glow)
- Three-panel workspace: File Browser, Email Inbox, Text Editor
- Dropdown menus via F-keys with proper z-ordering
- Status bar with file info, panel state, and scroll position

**Text Editor**
- Full text editing with multi-line support
- Text selection via Shift+Arrow keys
- Clipboard operations (Ctrl+C/X/V and menu)
- Vertical scrolling with auto-follow cursor
- Key repeat system (500ms delay, 75ms repeat)
- Home/End/Delete key support

**File Management**
- File browser scanning workspace for `.sv` and `.s` files
- Read-only protection for reference modules (letter-prefixed files)
- Editable level files (number-prefixed files like `1.sv`)
- Save/Load operations via F1 menu

**Email System**
- Level-based email loading from `emails/{level}/` directory
- Email parsing with From/Date/Subject headers
- Two-part inbox: email list with message preview
- Full email modal with scrolling (arrows, PgUp/PgDn, Home/End)
- Read/unread status tracking

**Level 1 Content**
- 5 instructional emails covering NOT gate implementation
- Reference `nand_gate.sv` module (read-only)
- Editable `1.sv` template for player solution
- Sample gate implementations for reference

### Integration Status with PySVSim

The companion simulator in `../pysvsim` is fully functional:
- Parses SystemVerilog modules with proper keyword handling (`signed`, `unsigned`, `reg`, `logic`)
- Generates truth tables for combinational logic
- Generates waveforms for sequential logic
- Counts NAND gates through design hierarchy
- 300+ test cases passing across 70+ module library

**Not Yet Integrated:**
- Automatic verification when player saves
- In-game display of simulation results
- Level completion detection
- NAND gate count display

## Project Structure

```
bitworks/                    # Game IDE (this repo)
├── main.py                  # pygame-ce application
├── workspace/               # Player files
│   ├── 1.sv                 # Level 1 solution file (editable)
│   ├── nand_gate.sv         # NAND primitive (read-only)
│   └── *.sv                 # Reference gates
├── emails/1/                # Level 1 educational content
└── *.md                     # Documentation

../pysvsim/                  # SystemVerilog simulator
├── pysvsim.py               # Parser and evaluator
├── test_runner.py           # Test execution framework
├── parts/                   # Verified module library
└── *.md                     # Documentation
```

## Next Steps

### Immediate Priority: Simulator Integration

1. **Add pysvsim subprocess call** - Run verification when player saves
2. **Parse simulation output** - Extract pass/fail and truth table
3. **Display results in-game** - Modal or panel showing verification status
4. **Level completion logic** - Detect when player solution is correct

### Short-term Enhancements

1. **Level 2 content** - AND gate from NAND gates
2. **Undo/Redo system** - Essential for code editing
3. **Syntax highlighting** - Basic Verilog keyword coloring
4. **Error display** - Show parser/simulation errors clearly

### Medium-term Goals

1. **Levels 3-10** - Build up to half adder, full adder, ALU components
2. **Assembly editor mode** - Support JASM for J16 processor
3. **Sound effects** - Retro boot sounds, keyboard clicks
4. **Progress persistence** - Save/load game state

### Long-term Vision

1. **Complete J16 CPU** - Playable computer architecture course
2. **FPGA export** - Generate synthesizable designs
3. **Multiplayer** - Compete on NAND gate efficiency
4. **Custom levels** - Community-created challenges

## Development Commands

```powershell
# Run BitWorks
cd bitworks
uv run main.py

# Test a player module with pysvsim
cd ../pysvsim
python test_runner.py ../bitworks/workspace/1.sv

# Run full pysvsim test suite
python test_runner.py parts/
python test_runner.py testing/
```

## Technical Debt

- **Single file**: `main.py` is ~1500 lines; consider splitting into modules
- **Global state**: Heavy use of globals; could refactor to class-based
- **No tests**: Game has no automated tests
- **Hardcoded paths**: Workspace and email paths are relative

## Dependencies

**BitWorks:**
- Python 3.13+
- pygame-ce 2.5.5+

**PySVSim:**
- Python 3.13+
- matplotlib (for PNG generation)
