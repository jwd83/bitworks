import pygame, sys, time, random, os

pygame.init()
pygame.mixer.init()

# Screen setup - Get fullscreen resolution and set to 16:9 if needed
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h

# Calculate 16:9 aspect ratio dimensions that fit the screen
aspect_ratio = 16 / 9
if screen_width / screen_height > aspect_ratio:
    # Screen is wider than 16:9, fit to height
    WIDTH = int(screen_height * aspect_ratio)
    HEIGHT = screen_height
else:
    # Screen is taller than 16:9, fit to width
    WIDTH = screen_width
    HEIGHT = int(screen_width / aspect_ratio)

# Create fullscreen display
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Retro PC Boot - Text Editor")

# Scale fonts based on screen size (larger fonts for bigger screens)
font_size = max(18, WIDTH // 60)  # Scale font with screen width
big_font_size = max(22, WIDTH // 50)
FONT = pygame.font.Font(pygame.font.match_font("couriernew", bold=True), font_size)
BIGFONT = pygame.font.Font(
    pygame.font.match_font("couriernew", bold=True), big_font_size
)
STATUS_BAR_HEIGHT = font_size + 8  # Height of status bar at bottom
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
MENU_BG = (0, 60, 0)
SELECTION_BG = (0, 128, 0)  # Darker green for selection background

boot_lines = [
    "JackROM BIOS (C) 1991 Jack Games Ltd.",
    "12-25-1991",
    "",
    "Main Processor: JG25",
    "Base Memory: 640 KB OK",
    "Extended Memory: 7424 KB",
    "128K CACHE MEMORY OK",
    "40MHz CPU Clock",
    "Detecting IDE Devices ...",
    "Primary Master: 40MB ST-251",
    "Primary Slave: None",
    "Starting DOS...",
    "",
    "C:\\>bitworks.exe",
    "Loading BitWorks Text Editor...",
    "",
    "",
]

boot_done = False
boot_index = 0
boot_timer = 0
boot_speed = 0.7

text_buffer = [""]
cursor_x, cursor_y = 0, 0
cursor_timer = 0  # Timer for CRT-style cursor fade effect
running = False

# Text selection system
selection_start_x, selection_start_y = None, None
selection_end_x, selection_end_y = None, None
selection_active = False
clipboard = ""  # Simple clipboard storage

# Workspace layout
LEFT_PANEL_WIDTH = WIDTH // 3  # Left third for browser and inbox
FILE_BROWSER_HEIGHT = HEIGHT // 2  # Top half of left panel
# Bottom half of left panel, accounting for status bar
INBOX_HEIGHT = HEIGHT - FILE_BROWSER_HEIGHT - STATUS_BAR_HEIGHT
EDITOR_WIDTH = WIDTH - LEFT_PANEL_WIDTH  # Right two-thirds for editor
EDITOR_X_OFFSET = LEFT_PANEL_WIDTH  # Editor starts after left panel

# Email inbox state
emails = []  # Will be loaded from files
current_level = 1  # Current game level

# Text editor scroll state
editor_scroll_offset = 0  # Current vertical scroll position in editor

# File browser state
workspace_files = []
selected_file_index = 0
current_file = f"{current_level}.sv"  # Currently opened file - level-based
file_read_only = False  # Track if current file is read-only
selected_email_index = 0
active_panel = "editor"  # "editor", "files", "inbox"
show_email_modal = False  # Whether to show full email modal
email_modal_content = ""  # Content for the modal
email_modal_scroll_offset = 0  # Current scroll position in modal
email_modal_content_lines = []  # Pre-processed lines for scrolling
email_modal_max_visible_lines = 0  # Max lines that fit in modal viewport

active_menu = None
menus = {
    "F1": ["New File", "Open File", "Save File", "Exit"],
    "F2": ["Cut", "Copy", "Paste"],
    "F3": ["Files Panel", "Inbox Panel", "Editor Panel"],  # Panel navigation
}

# Key repeat system
KEY_REPEAT_DELAY = 500  # 3/4 second initial delay (milliseconds)
KEY_REPEAT_INTERVAL = 75  # 1/4 second repeat interval (milliseconds)
key_states = {}  # Track key press states and timers
last_key_event = None  # Track the last processed key for repeats

# Keys that should repeat when held down
REPEAT_KEYS = {
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_BACKSPACE,
    pygame.K_DELETE,
    pygame.K_HOME,
    pygame.K_END,
    pygame.K_PAGEUP,
    pygame.K_PAGEDOWN,
}


def should_key_repeat(key):
    """Check if a key should repeat when held down"""
    return key in REPEAT_KEYS or (
        key >= 32 and key <= 126
    )  # Include printable ASCII characters


# File operations
def is_file_read_only(filename):
    """Determine if a file should be read-only based on its name.
    Files starting with numbers (like 1.sv, 2.sv, 33.s) are editable.
    Files starting with letters (like nand.sv, not.sv) are read-only.
    """
    # Note: .sv = SystemVerilog, .s = Assembly
    if not filename:
        return False
    return not filename[0].isdigit()


def ensure_workspace_dir():
    """Create workspace directory if it doesn't exist"""
    if not os.path.exists("workspace"):
        os.makedirs("workspace")


def save_file():
    """Save current text buffer to current file if not read-only"""
    global file_read_only, current_file
    if file_read_only:
        print(f"Cannot save: {current_file} is read-only")
        return False
    try:
        ensure_workspace_dir()
        file_path = os.path.join("workspace", current_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(text_buffer))
        print(f"Saved file: {current_file}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False


def load_file():
    """Load text from the current level file if it exists"""
    global text_buffer, cursor_x, cursor_y, current_file, file_read_only, editor_scroll_offset
    try:
        file_path = os.path.join("workspace", current_file)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    text_buffer = content.split("\n")
                else:
                    text_buffer = [""]
                cursor_x, cursor_y = 0, 0
                editor_scroll_offset = 0  # Reset scroll position
                file_read_only = is_file_read_only(current_file)
                return True
        return False
    except Exception as e:
        print(f"Error loading file: {e}")
        return False


def new_file():
    """Clear the text buffer for a new file"""
    global text_buffer, cursor_x, cursor_y, editor_scroll_offset
    text_buffer = [""]
    cursor_x, cursor_y = 0, 0
    editor_scroll_offset = 0  # Reset scroll position
    clear_selection()


def scan_workspace_files():
    """Scan workspace directory for .sv and .s files"""
    global workspace_files
    workspace_files = []

    try:
        ensure_workspace_dir()
        if os.path.exists("workspace"):
            for filename in sorted(os.listdir("workspace")):
                if filename.endswith((".sv", ".s")):
                    file_path = os.path.join("workspace", filename)
                    if os.path.isfile(file_path):
                        workspace_files.append(filename)
    except Exception as e:
        print(f"Error scanning workspace: {e}")

    # Ensure current file is in the list
    if current_file not in workspace_files and current_file:
        workspace_files.insert(0, current_file)


def load_file_by_name(filename):
    """Load a specific file by name"""
    global text_buffer, cursor_x, cursor_y, current_file, file_read_only, editor_scroll_offset
    try:
        ensure_workspace_dir()
        file_path = os.path.join("workspace", filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    text_buffer = content.split("\n")
                else:
                    text_buffer = [""]
                cursor_x, cursor_y = 0, 0
                editor_scroll_offset = 0  # Reset scroll position
                current_file = filename
                file_read_only = is_file_read_only(filename)
                clear_selection()
                readonly_status = " (read-ONLY)" if file_read_only else ""
                print(f"Loaded file: {filename}{readonly_status}")
                return True
        else:
            print(f"File not found: {filename}")
            return False
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        return False


def save_current_file():
    """Save current text buffer to the current file if not read-only"""
    global current_file, file_read_only
    if file_read_only:
        print(f"Cannot save: {current_file} is read-only")
        return False
    try:
        ensure_workspace_dir()
        file_path = os.path.join("workspace", current_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(text_buffer))
        print(f"Saved file: {current_file}")
        return True
    except Exception as e:
        print(f"Error saving file {current_file}: {e}")
        return False


def load_emails_for_level(level):
    """Load email messages from files for the specified level"""
    global emails
    emails = []

    email_dir = os.path.join("emails", str(level))
    if not os.path.exists(email_dir):
        print(f"Email directory not found: {email_dir}")
        return False

    try:
        # Get all .txt files in the level directory and sort them
        email_files = [f for f in os.listdir(email_dir) if f.endswith(".txt")]
        email_files.sort()

        for filename in email_files:
            file_path = os.path.join(email_dir, filename)
            email = parse_email_file(file_path)
            if email:
                emails.append(email)

        print(f"Loaded {len(emails)} emails for level {level}")
        return True

    except Exception as e:
        print(f"Error loading emails for level {level}: {e}")
        return False


def parse_email_file(file_path):
    """Parse an individual email file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        lines = content.split("\n")
        email = {"from": "", "date": "", "subject": "", "read": False, "content": ""}

        # Parse header fields
        content_start = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("From: "):
                email["from"] = line[6:]
            elif line.startswith("Date: "):
                email["date"] = line[6:]
            elif line.startswith("Subject: "):
                email["subject"] = line[9:]
            elif line.startswith("Read: "):
                email["read"] = line[6:].lower() == "true"
            elif line == "" and i > 0:  # First empty line after headers
                content_start = i + 1
                break

        # Everything after the headers is content
        if content_start < len(lines):
            email["content"] = "\n".join(lines[content_start:])

        return email

    except Exception as e:
        print(f"Error parsing email file {file_path}: {e}")
        return None


def switch_panel(panel_name):
    """Switch to a different panel"""
    global active_panel
    if panel_name in ["editor", "files", "inbox"]:
        active_panel = panel_name
        print(f"Switched to {panel_name} panel")
        return True
    return False


def show_email_modal_dialog(email_index):
    """Show full email content in modal dialog"""
    global show_email_modal, email_modal_content, email_modal_scroll_offset, email_modal_content_lines
    if email_index < len(emails):
        email = emails[email_index]
        email["read"] = True  # Mark as read when opened
        show_email_modal = True
        email_modal_scroll_offset = 0  # Reset scroll position

        email_modal_content = f"""From: {email['from']}
Date: {email['date']}
Subject: {email['subject']}

{'-' * 50}

{email['content']}

{'-' * 50}"""

        # Pre-process content for scrolling
        prepare_modal_content_for_scrolling()
        print(f"Opened email: {email['subject']}")


def close_email_modal():
    """Close the email modal dialog"""
    global show_email_modal, email_modal_content, email_modal_scroll_offset, email_modal_content_lines
    show_email_modal = False
    email_modal_content = ""
    email_modal_scroll_offset = 0
    email_modal_content_lines = []


def prepare_modal_content_for_scrolling():
    """Pre-process email modal content into wrapped lines for scrolling"""
    global email_modal_content_lines, email_modal_max_visible_lines

    # Calculate modal dimensions
    modal_width = int(WIDTH * 0.8)
    modal_height = int(HEIGHT * 0.8)
    header_height = font_size + 10
    available_width = modal_width - 40
    available_height = modal_height - header_height - 20

    modal_font = pygame.font.Font(
        pygame.font.match_font("couriernew"), max(14, int(font_size * 0.8))
    )
    line_height = font_size + 2
    email_modal_max_visible_lines = available_height // line_height

    # Process content into wrapped lines
    email_modal_content_lines = []
    content_lines = email_modal_content.split("\n")

    max_chars = available_width // (modal_font.size("M")[0])

    for content_line in content_lines:
        if len(content_line) <= max_chars:
            # Line fits as-is
            email_modal_content_lines.append(content_line)
        else:
            # Word wrap
            words = content_line.split(" ")
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= max_chars:
                    current_line = test_line
                else:
                    # Output current line and start new one
                    if current_line:
                        email_modal_content_lines.append(current_line)
                    current_line = word

            # Output final wrapped line
            if current_line:
                email_modal_content_lines.append(current_line)


def scroll_email_modal(direction, amount=1):
    """Scroll the email modal up or down"""
    global email_modal_scroll_offset

    if direction == "up":
        email_modal_scroll_offset = max(0, email_modal_scroll_offset - amount)
    elif direction == "down":
        max_scroll = max(
            0, len(email_modal_content_lines) - email_modal_max_visible_lines
        )
        email_modal_scroll_offset = min(max_scroll, email_modal_scroll_offset + amount)


def scroll_editor(direction, amount=1):
    """Scroll the text editor up or down"""
    global editor_scroll_offset
    
    if direction == "up":
        editor_scroll_offset = max(0, editor_scroll_offset - amount)
    elif direction == "down":
        # Calculate max scroll based on available content vs visible area
        # This will be calculated dynamically based on editor dimensions
        max_scroll = max(0, len(text_buffer) - get_editor_max_visible_lines())
        editor_scroll_offset = min(max_scroll, editor_scroll_offset + amount)


def get_editor_max_visible_lines():
    """Calculate how many lines can fit in the editor viewport"""
    line_height = font_size + 4
    header_height = line_height + 4
    menu_height = font_size + 14
    available_height = HEIGHT - menu_height - header_height - 10 - STATUS_BAR_HEIGHT  # Total minus menu, header, margin, and status bar
    return max(1, available_height // line_height)


def ensure_cursor_visible():
    """Ensure the cursor is visible by adjusting scroll offset if needed"""
    global editor_scroll_offset
    
    max_visible_lines = get_editor_max_visible_lines()
    
    # If cursor is above visible area, scroll up to show it
    if cursor_y < editor_scroll_offset:
        editor_scroll_offset = cursor_y
    
    # If cursor is below visible area, scroll down to show it
    elif cursor_y >= editor_scroll_offset + max_visible_lines:
        editor_scroll_offset = cursor_y - max_visible_lines + 1
        # Ensure we don't scroll past the beginning
        editor_scroll_offset = max(0, editor_scroll_offset)


def handle_panel_navigation(event):
    """Handle navigation within panels"""
    global selected_file_index, selected_email_index, workspace_files, emails

    if active_panel == "files":
        if event.key == pygame.K_UP:
            selected_file_index = max(0, selected_file_index - 1)
        elif event.key == pygame.K_DOWN:
            selected_file_index = min(len(workspace_files) - 1, selected_file_index + 1)
        elif event.key == pygame.K_RETURN:
            if workspace_files and selected_file_index < len(workspace_files):
                filename = workspace_files[selected_file_index]
                if load_file_by_name(filename):
                    switch_panel("editor")

    elif active_panel == "inbox":
        if event.key == pygame.K_UP:
            selected_email_index = max(0, selected_email_index - 1)
        elif event.key == pygame.K_DOWN:
            selected_email_index = min(len(emails) - 1, selected_email_index + 1)
        elif event.key == pygame.K_RETURN:
            if selected_email_index < len(emails):
                show_email_modal_dialog(selected_email_index)


def clear_selection():
    """Clear the current text selection"""
    global selection_start_x, selection_start_y, selection_end_x, selection_end_y, selection_active
    selection_start_x = selection_start_y = None
    selection_end_x = selection_end_y = None
    selection_active = False


def start_selection(x, y):
    """Start a text selection at the given position"""
    global selection_start_x, selection_start_y, selection_active
    selection_start_x, selection_start_y = x, y
    selection_active = True


def update_selection(x, y):
    """Update the selection end position"""
    global selection_end_x, selection_end_y
    selection_end_x, selection_end_y = x, y


def get_selection_bounds():
    """Get normalized selection bounds (start always before end)"""
    if not selection_active or selection_start_x is None or selection_end_x is None:
        return None

    start_y, start_x = selection_start_y, selection_start_x
    end_y, end_x = selection_end_y, selection_end_x

    # Normalize so start is always before end
    if start_y > end_y or (start_y == end_y and start_x > end_x):
        start_y, end_y = end_y, start_y
        start_x, end_x = end_x, start_x

    return (start_x, start_y, end_x, end_y)


def get_selected_text():
    """Get the currently selected text"""
    bounds = get_selection_bounds()
    if not bounds:
        return ""

    start_x, start_y, end_x, end_y = bounds

    if start_y == end_y:
        # Single line selection
        return text_buffer[start_y][start_x:end_x]
    else:
        # Multi-line selection
        selected_lines = []

        # First line (from start_x to end)
        selected_lines.append(text_buffer[start_y][start_x:])

        # Middle lines (full lines)
        for y in range(start_y + 1, end_y):
            selected_lines.append(text_buffer[y])

        # Last line (from beginning to end_x)
        selected_lines.append(text_buffer[end_y][:end_x])

        return "\n".join(selected_lines)


def delete_selected_text():
    """Delete the currently selected text and return the cursor to selection start"""
    global text_buffer, cursor_x, cursor_y
    bounds = get_selection_bounds()
    if not bounds:
        return False

    start_x, start_y, end_x, end_y = bounds

    if start_y == end_y:
        # Single line deletion
        line = text_buffer[start_y]
        text_buffer[start_y] = line[:start_x] + line[end_x:]
    else:
        # Multi-line deletion
        # Combine the remaining parts of first and last lines
        combined_line = text_buffer[start_y][:start_x] + text_buffer[end_y][end_x:]

        # Remove all lines in selection
        del text_buffer[start_y : end_y + 1]

        # Insert the combined line
        text_buffer.insert(start_y, combined_line)

    # Position cursor at selection start
    cursor_x, cursor_y = start_x, start_y
    clear_selection()
    return True


def copy_to_clipboard():
    """Copy selected text to clipboard"""
    global clipboard
    selected = get_selected_text()
    if selected:
        clipboard = selected
        print(f"Copied: {selected[:50]}{'...' if len(selected) > 50 else ''}")
        return True
    return False


def cut_to_clipboard():
    """Cut selected text to clipboard"""
    global clipboard
    selected = get_selected_text()
    if selected and delete_selected_text():
        clipboard = selected
        print(f"Cut: {selected[:50]}{'...' if len(selected) > 50 else ''}")
        return True
    return False


def paste_from_clipboard():
    """Paste text from clipboard at cursor position"""
    global text_buffer, cursor_x, cursor_y, clipboard
    if not clipboard:
        print("Clipboard is empty")
        return False

    # If there's a selection, delete it first
    if selection_active:
        delete_selected_text()

    # Split clipboard content into lines
    clipboard_lines = clipboard.split("\n")

    if len(clipboard_lines) == 1:
        # Single line paste
        line = text_buffer[cursor_y]
        text_buffer[cursor_y] = line[:cursor_x] + clipboard + line[cursor_x:]
        cursor_x += len(clipboard)
    else:
        # Multi-line paste
        current_line = text_buffer[cursor_y]
        before_cursor = current_line[:cursor_x]
        after_cursor = current_line[cursor_x:]

        # First line: before cursor + first clipboard line
        text_buffer[cursor_y] = before_cursor + clipboard_lines[0]

        # Middle lines: insert full lines
        for i, line in enumerate(clipboard_lines[1:-1], 1):
            text_buffer.insert(cursor_y + i, line)

        # Last line: last clipboard line + after cursor
        text_buffer.insert(
            cursor_y + len(clipboard_lines) - 1, clipboard_lines[-1] + after_cursor
        )

        # Update cursor position to end of paste
        cursor_y += len(clipboard_lines) - 1
        cursor_x = len(clipboard_lines[-1])

    print(f"Pasted: {clipboard[:50]}{'...' if len(clipboard) > 50 else ''}")
    return True


def update_key_repeat():
    """Update key repeat timers and generate repeat events"""
    global key_states, last_key_event
    current_time = pygame.time.get_ticks()

    # Get currently pressed keys
    pressed_keys = pygame.key.get_pressed()

    # Remove keys that are no longer pressed
    keys_to_remove = []
    for key in key_states:
        if not pressed_keys[key]:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del key_states[key]

    # Check for keys that should repeat
    for key in key_states:
        key_data = key_states[key]
        time_held = current_time - key_data["start_time"]

        if not key_data["repeating"] and time_held >= KEY_REPEAT_DELAY:
            # Start repeating
            key_data["repeating"] = True
            key_data["last_repeat"] = current_time
            return key  # Return the key to repeat
        elif (
            key_data["repeating"]
            and (current_time - key_data["last_repeat"]) >= KEY_REPEAT_INTERVAL
        ):
            # Continue repeating
            key_data["last_repeat"] = current_time
            return key  # Return the key to repeat

    return None


def handle_key_press(key, event=None):
    """Handle a key press, either from event or repeat"""
    global key_states, last_key_event
    current_time = pygame.time.get_ticks()

    # If this is a new key press (not a repeat), track it if it should repeat
    if event and key not in key_states and should_key_repeat(key):
        key_states[key] = {
            "start_time": current_time,
            "repeating": False,
            "last_repeat": 0,
        }
        last_key_event = event

    # Create a synthetic event for repeats
    if not event and last_key_event:
        # Create a synthetic event based on the last real event
        event = type(
            "Event",
            (),
            {
                "type": pygame.KEYDOWN,
                "key": key,
                "unicode": (
                    last_key_event.unicode if hasattr(last_key_event, "unicode") else ""
                ),
                "mod": last_key_event.mod if hasattr(last_key_event, "mod") else 0,
            },
        )()

    return event


def handle_menu_action(menu, item_index):
    """Handle menu item selection"""
    global running

    if menu == "F1":
        menu_items = menus["F1"]
        if item_index < len(menu_items):
            action = menu_items[item_index]
            if action == "New File":
                new_file()
                print("New file created")
            elif action == "Open File":
                switch_panel("files")
                print("Switched to files panel - select a file to open")
            elif action == "Save File":
                if save_current_file():
                    print(f"Saved current file: {current_file}")
                else:
                    print("Error saving file")
            elif action == "Exit":
                return False  # Signal to quit
    elif menu == "F2":
        menu_items = menus["F2"]
        if item_index < len(menu_items):
            action = menu_items[item_index]
            if action == "Cut":
                if file_read_only:
                    print(f"Cannot cut: {current_file} is read-only")
                elif not cut_to_clipboard():
                    print("Nothing to cut (no selection)")
            elif action == "Copy":
                if not copy_to_clipboard():
                    print("Nothing to copy (no selection)")
            elif action == "Paste":
                if file_read_only:
                    print(f"Cannot paste: {current_file} is read-only")
                elif not paste_from_clipboard():
                    print("Nothing to paste (clipboard empty)")
    elif menu == "F3":
        menu_items = menus["F3"]
        if item_index < len(menu_items):
            action = menu_items[item_index]
            if action == "Files Panel":
                switch_panel("files")
            elif action == "Inbox Panel":
                switch_panel("inbox")
            elif action == "Editor Panel":
                switch_panel("editor")

    return True  # Continue running


def draw_boot_screen():
    screen.fill(BLACK)
    # Scale spacing based on screen size
    x_margin = WIDTH // 40  # Scale margin
    y_start = HEIGHT // 15  # Scale starting Y position
    line_spacing = font_size + 6  # Scale line spacing

    for i in range(boot_index):
        line = boot_lines[i]
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (x_margin, y_start + i * line_spacing))

    # Show skip instruction in bottom-right corner
    skip_text = "Press ENTER or ESC to skip"
    skip_font = pygame.font.Font(
        pygame.font.match_font("couriernew"), max(14, int(font_size * 0.8))
    )
    skip_surface = skip_font.render(skip_text, True, GREEN)
    skip_rect = skip_surface.get_rect()
    skip_rect.bottomright = (WIDTH - 10, HEIGHT - 10)
    screen.blit(skip_surface, skip_rect)

    pygame.display.flip()


def draw_workspace():
    """Draw the multi-column workspace layout"""
    screen.fill(BLACK)

    # Scale UI elements based on screen size
    menu_height = font_size + 14
    line_height = font_size + 4

    # Draw menu bar across full width
    draw_menu_bar(menu_height)

    # Draw vertical separator lines
    pygame.draw.line(
        screen, GREEN, (LEFT_PANEL_WIDTH, menu_height), (LEFT_PANEL_WIDTH, HEIGHT), 1
    )
    pygame.draw.line(
        screen,
        GREEN,
        (0, FILE_BROWSER_HEIGHT),
        (LEFT_PANEL_WIDTH, FILE_BROWSER_HEIGHT),
        1,
    )

    # Draw file browser (top-left)
    draw_file_browser(menu_height, FILE_BROWSER_HEIGHT, line_height)

    # Draw email inbox (bottom-left, above status bar)
    draw_email_inbox(FILE_BROWSER_HEIGHT, HEIGHT - STATUS_BAR_HEIGHT, line_height)

    # Draw text editor (right two-thirds, adjusted for status bar)
    editor_height = HEIGHT - menu_height - STATUS_BAR_HEIGHT
    draw_text_editor(
        EDITOR_X_OFFSET, menu_height, EDITOR_WIDTH, editor_height, line_height
    )
    
    # Draw status bar (only if no modal is open)
    if not show_email_modal:
        draw_status_bar()

    # Draw email modal if active (on top of everything)
    draw_email_modal()
    
    # Draw dropdown menus last so they appear above everything else
    if active_menu:
        x_margin = WIDTH // 50
        menu_spacing = WIDTH // 8
        draw_dropdown_menu(menu_height, x_margin, menu_spacing)

    pygame.display.flip()


def draw_menu_bar(menu_height):
    """Draw the menu bar across the top"""
    pygame.draw.rect(screen, MENU_BG, (0, 0, WIDTH, menu_height))

    # Update menu labels to reflect new functionality
    fkeys = ["F1-File", "F2-Edit", "F3-View"]
    x_margin = WIDTH // 50
    menu_spacing = WIDTH // 8
    x = x_margin

    for label in fkeys:
        txt = FONT.render(label, True, GREEN)
        screen.blit(txt, (x, (menu_height - font_size) // 2))
        x += menu_spacing


def draw_dropdown_menu(menu_height, x_margin, menu_spacing):
    """Draw dropdown menu with enhanced visibility"""
    menu_items = menus[active_menu]
    idx = ["F1", "F2", "F3"].index(active_menu)
    x = x_margin + menu_spacing * idx
    y = menu_height
    menu_item_height = font_size + 8
    menu_item_width = WIDTH // 8
    
    # Calculate total menu height
    total_menu_height = len(menu_items) * menu_item_height
    
    # Draw subtle shadow (offset by 2 pixels)
    shadow_color = (20, 20, 20)  # Very dark shadow
    pygame.draw.rect(screen, shadow_color, (x + 2, y + 2, menu_item_width, total_menu_height))
    
    # Draw menu background
    pygame.draw.rect(screen, BLACK, (x, y, menu_item_width, total_menu_height))
    
    # Draw menu border
    pygame.draw.rect(screen, GREEN, (x, y, menu_item_width, total_menu_height), 2)

    # Draw menu items
    current_y = y
    for i, item in enumerate(menu_items):
        # Draw item background (darker gray for individual items)
        pygame.draw.rect(screen, GRAY, (x + 2, current_y + 2, menu_item_width - 4, menu_item_height - 2))
        
        # Draw item text
        fkey_text = f"F{i+1}-{item}"
        t = FONT.render(fkey_text, True, GREEN)
        screen.blit(t, (x + 8, current_y + (menu_item_height - font_size) // 2))
        
        current_y += menu_item_height


def draw_file_browser(y_start, y_end, line_height):
    """Draw the file browser panel"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "files" else GRAY
    pygame.draw.rect(screen, header_bg, (0, y_start, LEFT_PANEL_WIDTH, header_height))

    header_text = FONT.render("FILES (.sv/.s)", True, GREEN)
    screen.blit(header_text, (5, y_start + 2))

    # File list
    y = y_start + header_height + 5
    max_files = (FILE_BROWSER_HEIGHT - header_height - 10) // line_height

    for i, filename in enumerate(workspace_files[:max_files]):
        if i == selected_file_index and active_panel == "files":
            # Highlight selected file
            pygame.draw.rect(
                screen, SELECTION_BG, (2, y - 2, LEFT_PANEL_WIDTH - 4, line_height)
            )

        # Show file type icon with better detection
        if filename.endswith(".sv"):
            icon = "V"  # SystemVerilog
        elif filename.endswith(".v"):
            icon = "V"  # Legacy Verilog (for backward compatibility)
        elif filename.endswith(".s"):
            icon = "S"  # Assembly
        else:
            icon = "?"

        icon_text = FONT.render(f"[{icon}]", True, GREEN)
        screen.blit(icon_text, (5, y))

        # Show filename (truncate if too long) - account for icon width
        icon_width = FONT.size(f"[{icon}] ")[0]
        max_name_width = LEFT_PANEL_WIDTH - icon_width - 25
        name_text = filename
        if FONT.size(name_text)[0] > max_name_width:
            while (
                FONT.size(name_text + "...")[0] > max_name_width and len(name_text) > 0
            ):
                name_text = name_text[:-1]
            name_text += "..."

        file_text = FONT.render(name_text, True, GREEN)
        screen.blit(file_text, (5 + icon_width, y))

        # Mark current file
        if filename == current_file:
            current_marker = FONT.render("*", True, GREEN)
            screen.blit(current_marker, (LEFT_PANEL_WIDTH - 15, y))

        y += line_height


def draw_email_inbox(y_start, y_end, line_height):
    """Draw the email inbox panel with message preview"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "inbox" else GRAY
    pygame.draw.rect(screen, header_bg, (0, y_start, LEFT_PANEL_WIDTH, header_height))

    header_text = FONT.render("INBOX", True, GREEN)
    screen.blit(header_text, (5, y_start + 2))

    # Calculate split: top half for email list, bottom half for message preview
    inbox_total_height = y_end - y_start - header_height - 5
    email_list_height = inbox_total_height // 2
    message_preview_height = inbox_total_height - email_list_height

    # Email list (top half)
    y = y_start + header_height + 5
    max_emails = email_list_height // line_height

    for i, email in enumerate(emails[:max_emails]):
        if i == selected_email_index and active_panel == "inbox":
            # Highlight selected email
            pygame.draw.rect(
                screen, SELECTION_BG, (2, y - 2, LEFT_PANEL_WIDTH - 4, line_height)
            )

        # Show read/unread status
        status = " " if email["read"] else "●"
        status_text = FONT.render(status, True, GREEN)
        screen.blit(status_text, (5, y))

        # Show subject (truncate if too long)
        max_subject_width = LEFT_PANEL_WIDTH - 25
        subject = email["subject"]
        if FONT.size(subject)[0] > max_subject_width:
            while (
                FONT.size(subject + "...")[0] > max_subject_width and len(subject) > 0
            ):
                subject = subject[:-1]
            subject += "..."

        subject_text = FONT.render(subject, True, GREEN)
        screen.blit(subject_text, (15, y))

        y += line_height

    # Separator line between email list and message preview
    separator_y = y_start + header_height + 5 + email_list_height
    pygame.draw.line(
        screen, GREEN, (0, separator_y), (LEFT_PANEL_WIDTH, separator_y), 1
    )

    # Message preview (bottom half)
    draw_message_preview(separator_y + 2, y_end, line_height)


def draw_message_preview(y_start, y_end, line_height):
    """Draw the selected message content preview"""
    if selected_email_index < len(emails):
        email = emails[selected_email_index]

        # Message header
        preview_y = y_start + 5

        # From line (truncate if too long)
        from_line = f"From: {email['from']}"
        max_preview_width = LEFT_PANEL_WIDTH - 15
        if FONT.size(from_line)[0] > max_preview_width:
            while (
                FONT.size(from_line + "...")[0] > max_preview_width
                and len(from_line) > 5
            ):
                from_line = from_line[:-1]
            from_line += "..."
        from_text = FONT.render(from_line, True, GREEN)
        screen.blit(from_text, (5, preview_y))
        preview_y += line_height

        # Date line (truncate if too long)
        date_line = f"Date: {email['date']}"
        if FONT.size(date_line)[0] > max_preview_width:
            while (
                FONT.size(date_line + "...")[0] > max_preview_width
                and len(date_line) > 5
            ):
                date_line = date_line[:-1]
            date_line += "..."
        date_text = FONT.render(date_line, True, GREEN)
        screen.blit(date_text, (5, preview_y))
        preview_y += line_height

        # Subject line (truncate if too long)
        subject_line = f"Subject: {email['subject']}"
        if FONT.size(subject_line)[0] > max_preview_width:
            while (
                FONT.size(subject_line + "...")[0] > max_preview_width
                and len(subject_line) > 8
            ):
                subject_line = subject_line[:-1]
            subject_line += "..."
        subject_text = FONT.render(subject_line, True, GREEN)
        screen.blit(subject_text, (5, preview_y))
        preview_y += line_height + 5

        # Message content (wrap and truncate to fit) - reserve space for hint
        hint_space = (
            line_height + 10
        )  # Reserve space for the "ENTER for full message" hint
        available_height = y_end - preview_y - hint_space
        max_lines = max(1, available_height // line_height)  # Ensure at least 1 line

        content_lines = email["content"].split("\n")
        lines_shown = 0

        for content_line in content_lines:
            if lines_shown >= max_lines:
                break

            # Word wrap long lines - constrain to panel width
            max_content_width = LEFT_PANEL_WIDTH - 15

            # Check if line fits within panel width
            if FONT.size(content_line)[0] <= max_content_width:
                # Line fits as-is
                line_text = FONT.render(content_line, True, GREEN)
                screen.blit(line_text, (5, preview_y))
                preview_y += line_height
                lines_shown += 1
            else:
                # Wrap line by pixels, not characters
                words = content_line.split(" ")
                current_line = ""

                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if FONT.size(test_line)[0] <= max_content_width:
                        current_line = test_line
                    else:
                        # Output current line and start new one
                        if current_line:
                            line_text = FONT.render(current_line, True, GREEN)
                            screen.blit(line_text, (5, preview_y))
                            preview_y += line_height
                            lines_shown += 1
                            if lines_shown >= max_lines:
                                break
                        current_line = word

                        # If single word is too long, truncate it
                        if FONT.size(current_line)[0] > max_content_width:
                            while (
                                FONT.size(current_line + "...")[0] > max_content_width
                                and len(current_line) > 1
                            ):
                                current_line = current_line[:-1]
                            current_line += "..."

                # Output final line if any
                if current_line and lines_shown < max_lines:
                    line_text = FONT.render(current_line, True, GREEN)
                    screen.blit(line_text, (5, preview_y))
                    lines_shown += 1

        # Show "Press ENTER for full message" hint if message was truncated
        if lines_shown >= max_lines or len(content_lines) > lines_shown:
            hint_y = y_end - line_height - 5
            hint_text = FONT.render("[ENTER for full message]", True, GREEN)

            # Draw black background behind the hint to ensure visibility
            hint_rect = hint_text.get_rect()
            hint_rect.x = 5
            hint_rect.y = hint_y
            hint_rect.width = min(
                hint_rect.width + 4, LEFT_PANEL_WIDTH - 10
            )  # Add padding, respect panel bounds
            hint_rect.height = hint_rect.height + 2  # Add padding
            pygame.draw.rect(screen, BLACK, hint_rect)

            screen.blit(hint_text, (5, hint_y))


def draw_text_editor(x_start, y_start, width, height, line_height):
    """Draw the text editor panel with scrolling support"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "editor" else GRAY
    pygame.draw.rect(screen, header_bg, (x_start, y_start, width, header_height))

    readonly_status = " (READ-ONLY)" if file_read_only else ""
    header_text = FONT.render(f"EDITOR - {current_file}{readonly_status}", True, GREEN)
    screen.blit(header_text, (x_start + 5, y_start + 2))

    # Text area (reserve space for status bar)
    text_y_start = y_start + header_height + 5
    text_x_margin = x_start + 10
    available_text_height = height - header_height - 10 - STATUS_BAR_HEIGHT
    max_lines = available_text_height // line_height
    
    # Calculate which lines to display based on scroll offset
    start_line = editor_scroll_offset
    end_line = min(start_line + max_lines, len(text_buffer))
    
    # Draw text with selection highlighting (only if editor is active)
    bounds = (
        get_selection_bounds()
        if selection_active and active_panel == "editor"
        else None
    )

    for display_y, buffer_y in enumerate(range(start_line, end_line)):
        line = text_buffer[buffer_y]
        line_y = text_y_start + display_y * line_height

        # Draw selection background if this line is selected
        if bounds:
            start_x, start_y, end_x, end_y = bounds
            if start_y <= buffer_y <= end_y:
                # Calculate selection bounds for this line
                if buffer_y == start_y and buffer_y == end_y:
                    sel_start = (
                        text_x_margin + FONT.size(line[:start_x])[0]
                        if line
                        else text_x_margin
                    )
                    sel_end = (
                        text_x_margin + FONT.size(line[:end_x])[0]
                        if line
                        else text_x_margin
                    )
                elif buffer_y == start_y:
                    sel_start = (
                        text_x_margin + FONT.size(line[:start_x])[0]
                        if line
                        else text_x_margin
                    )
                    sel_end = (
                        text_x_margin + FONT.size(line)[0] if line else text_x_margin
                    )
                elif buffer_y == end_y:
                    sel_start = text_x_margin
                    sel_end = (
                        text_x_margin + FONT.size(line[:end_x])[0]
                        if line
                        else text_x_margin
                    )
                else:
                    sel_start = text_x_margin
                    sel_end = (
                        text_x_margin + FONT.size(line)[0] if line else text_x_margin
                    )

                sel_width = max(10, sel_end - sel_start)
                pygame.draw.rect(
                    screen, SELECTION_BG, (sel_start, line_y, sel_width, line_height)
                )

        # Draw text
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (text_x_margin, line_y))
    
    # Draw scroll indicators if there's more content than visible
    if len(text_buffer) > max_lines:
        draw_editor_scroll_indicators(x_start, y_start, width, height, header_height, max_lines)

    # Draw cursor (only if editor is active)
    if active_panel == "editor":
        draw_cursor(text_x_margin, text_y_start, line_height)


def draw_editor_scroll_indicators(x_start, y_start, width, height, header_height, max_visible_lines):
    """Draw scroll indicators for the text editor"""
    # Scroll bar area (right side of editor, above status bar)
    scroll_bar_x = x_start + width - 20
    scroll_bar_y = y_start + header_height + 5
    scroll_bar_width = 12
    scroll_bar_height = height - header_height - 10 - STATUS_BAR_HEIGHT
    
    # Draw scroll bar background
    pygame.draw.rect(screen, GRAY, (scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))
    
    # Calculate scroll thumb position and size
    total_lines = len(text_buffer)
    if total_lines > max_visible_lines:
        thumb_height = max(10, int(scroll_bar_height * max_visible_lines / total_lines))
        thumb_y = scroll_bar_y + int(scroll_bar_height * editor_scroll_offset / total_lines)
        
        # Ensure thumb doesn't go past the bottom
        if thumb_y + thumb_height > scroll_bar_y + scroll_bar_height:
            thumb_y = scroll_bar_y + scroll_bar_height - thumb_height
        
        # Draw scroll thumb
        pygame.draw.rect(screen, GREEN, (scroll_bar_x, thumb_y, scroll_bar_width, thumb_height))


def draw_status_bar():
    """Draw the status bar at the bottom of the screen"""
    status_y = HEIGHT - STATUS_BAR_HEIGHT
    
    # Draw status bar background
    pygame.draw.rect(screen, MENU_BG, (0, status_y, WIDTH, STATUS_BAR_HEIGHT))
    pygame.draw.line(screen, GREEN, (0, status_y), (WIDTH, status_y), 1)  # Top border
    
    # Left side: File info
    readonly_status = " (READ-ONLY)" if file_read_only else ""
    file_info = f"File: {current_file}{readonly_status}"
    file_surface = FONT.render(file_info, True, GREEN)
    screen.blit(file_surface, (10, status_y + 4))
    
    # Center: Panel info
    panel_info = f"Panel: {active_panel.title()}"
    panel_surface = FONT.render(panel_info, True, GREEN)
    panel_x = (WIDTH - panel_surface.get_width()) // 2
    screen.blit(panel_surface, (panel_x, status_y + 4))
    
    # Right side: Editor scroll info (only if editor is active and has scrollable content)
    if active_panel == "editor" and len(text_buffer) > get_editor_max_visible_lines():
        max_visible = get_editor_max_visible_lines()
        current_line = cursor_y + 1
        total_lines = len(text_buffer)
        visible_start = editor_scroll_offset + 1
        visible_end = min(editor_scroll_offset + max_visible, total_lines)
        
        scroll_info = f"Line {current_line}/{total_lines} | View {visible_start}-{visible_end}"
        scroll_surface = FONT.render(scroll_info, True, GREEN)
        scroll_x = WIDTH - scroll_surface.get_width() - 10
        screen.blit(scroll_surface, (scroll_x, status_y + 4))
    elif active_panel == "editor":
        # Show simple line info when not scrollable
        current_line = cursor_y + 1
        total_lines = len(text_buffer)
        line_info = f"Line {current_line}/{total_lines}"
        line_surface = FONT.render(line_info, True, GREEN)
        line_x = WIDTH - line_surface.get_width() - 10
        screen.blit(line_surface, (line_x, status_y + 4))


def draw_cursor(text_x_margin, text_y_start, line_height):
    """Draw the text cursor with CRT-style fade effect"""
    global cursor_timer
    
    if cursor_y >= len(text_buffer):
        return
    
    # Check if cursor is in visible area
    max_visible_lines = get_editor_max_visible_lines()
    if cursor_y < editor_scroll_offset or cursor_y >= editor_scroll_offset + max_visible_lines:
        return  # Cursor is not visible, don't draw it
        
    # Update cursor timer
    cursor_timer += clock.get_time()
    
    # Full fade cycle: 1200ms for slower, more CRT-like timing
    fade_cycle_duration = 1200
    fade_duration = 600  # Time for fade out or fade in
    
    # Reset timer after full cycle
    if cursor_timer >= fade_cycle_duration:
        cursor_timer = 0
    
    # Calculate cursor position (adjusted for scroll)
    cx = text_x_margin + FONT.size(text_buffer[cursor_y][:cursor_x])[0]
    cy = text_y_start + (cursor_y - editor_scroll_offset) * line_height
    cursor_width = max(2, font_size // 9)
    
    # Calculate fade opacity with smoother easing
    if cursor_timer <= fade_duration:
        # First half: fade out (1.0 -> 0.05) with ease-in
        progress = cursor_timer / fade_duration
        # Use sine wave for smoother transition
        eased_progress = (1 - __import__('math').cos(progress * __import__('math').pi)) / 2
        opacity = 1.0 - (eased_progress * 0.95)  # Fade from 1.0 to 0.05
    else:
        # Second half: fade in (0.05 -> 1.0) with ease-out
        progress = (cursor_timer - fade_duration) / fade_duration
        # Use sine wave for smoother transition
        eased_progress = (1 - __import__('math').cos(progress * __import__('math').pi)) / 2
        opacity = 0.05 + (eased_progress * 0.95)  # Fade from 0.05 to 1.0
    
    # Ensure opacity stays in valid range
    opacity = max(0.05, min(opacity, 1.0))
    
    # Calculate faded color
    faded_color = (
        int(GREEN[0] * opacity),
        int(GREEN[1] * opacity),
        int(GREEN[2] * opacity),
    )
    
    # Draw cursor with faded color and slight glow effect
    # Draw a slightly larger, more transparent cursor behind for glow
    if opacity > 0.3:  # Only add glow when cursor is relatively bright
        glow_opacity = opacity * 0.3  # Glow is 30% of main cursor opacity
        glow_color = (
            int(GREEN[0] * glow_opacity),
            int(GREEN[1] * glow_opacity),
            int(GREEN[2] * glow_opacity),
        )
        # Draw glow (larger, more transparent)
        pygame.draw.rect(screen, glow_color, (cx - 1, cy - 1, cursor_width * 5 + 2, font_size + 2), 1)
    
    # Draw main cursor
    pygame.draw.rect(screen, faded_color, (cx, cy, cursor_width * 5, font_size), 1)


def draw_email_modal():
    """Draw the full email modal dialog with scrolling support"""
    if not show_email_modal or not email_modal_content_lines:
        return

    # Modal dimensions (80% of screen)
    modal_width = int(WIDTH * 0.8)
    modal_height = int(HEIGHT * 0.8)
    modal_x = (WIDTH - modal_width) // 2
    modal_y = (HEIGHT - modal_height) // 2

    # Draw modal background with border
    pygame.draw.rect(screen, BLACK, (modal_x, modal_y, modal_width, modal_height))
    pygame.draw.rect(screen, GREEN, (modal_x, modal_y, modal_width, modal_height), 2)

    # Draw modal header
    header_height = font_size + 10
    pygame.draw.rect(screen, MENU_BG, (modal_x, modal_y, modal_width, header_height))

    header_text = "EMAIL MESSAGE - UP/DOWN or PgUp/PgDn to scroll, HOME/END to jump, any key to close"
    header_surface = FONT.render(header_text, True, GREEN)
    header_x = modal_x + (modal_width - header_surface.get_width()) // 2
    screen.blit(header_surface, (header_x, modal_y + 5))

    # Draw scrolling content
    content_y = modal_y + header_height + 10
    content_x = modal_x + 20

    modal_font = pygame.font.Font(
        pygame.font.match_font("couriernew"), max(14, int(font_size * 0.8))
    )
    line_height = font_size + 2

    # Render visible lines based on scroll offset
    start_line = email_modal_scroll_offset
    end_line = min(
        start_line + email_modal_max_visible_lines, len(email_modal_content_lines)
    )

    for i in range(start_line, end_line):
        line = email_modal_content_lines[i]
        line_surface = modal_font.render(line, True, GREEN)
        screen.blit(line_surface, (content_x, content_y))
        content_y += line_height

    # Draw scroll indicators if content is scrollable
    if len(email_modal_content_lines) > email_modal_max_visible_lines:
        # Draw scroll position indicator
        scroll_indicator_x = modal_x + modal_width - 30
        scroll_indicator_y = modal_y + header_height + 10
        scroll_indicator_height = modal_height - header_height - 20

        # Scroll bar background
        pygame.draw.rect(
            screen,
            GRAY,
            (scroll_indicator_x, scroll_indicator_y, 10, scroll_indicator_height),
        )

        # Scroll bar thumb
        total_lines = len(email_modal_content_lines)
        thumb_height = max(
            10,
            int(scroll_indicator_height * email_modal_max_visible_lines / total_lines),
        )
        thumb_y = scroll_indicator_y + int(
            scroll_indicator_height * email_modal_scroll_offset / total_lines
        )
        pygame.draw.rect(screen, GREEN, (scroll_indicator_x, thumb_y, 10, thumb_height))

        # Show scroll hints
        if email_modal_scroll_offset > 0:
            up_hint = modal_font.render("↑ UP", True, GREEN)
            screen.blit(
                up_hint, (modal_x + modal_width - 60, modal_y + header_height + 5)
            )

        if email_modal_scroll_offset < total_lines - email_modal_max_visible_lines:
            down_hint = modal_font.render("↓ DOWN", True, GREEN)
            screen.blit(
                down_hint, (modal_x + modal_width - 70, modal_y + modal_height - 25)
            )


def handle_text_input(event):
    global cursor_x, cursor_y, file_read_only
    line = text_buffer[cursor_y]

    # Get modifier keys
    keys = pygame.key.get_pressed()
    shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

    # Handle clipboard shortcuts first
    if ctrl_pressed:
        if event.key == pygame.K_c:
            copy_to_clipboard()
            return
        elif event.key == pygame.K_x:
            if file_read_only:
                print(f"Cannot cut: {current_file} is read-only")
                return
            cut_to_clipboard()
            return
        elif event.key == pygame.K_v:
            if file_read_only:
                print(f"Cannot paste: {current_file} is read-only")
                return
            paste_from_clipboard()
            return
        elif event.key == pygame.K_a:
            # Select all
            if text_buffer:
                clear_selection()
                start_selection(0, 0)
                last_line = len(text_buffer) - 1
                last_char = len(text_buffer[last_line])
                update_selection(last_char, last_line)
            return

    # Start selection if Shift is pressed and not already selecting
    if shift_pressed and not selection_active:
        start_selection(cursor_x, cursor_y)

    # Store old cursor position for selection update
    old_cursor_x, old_cursor_y = cursor_x, cursor_y

    if event.key == pygame.K_BACKSPACE:
        if file_read_only:
            print(f"Cannot edit: {current_file} is read-only")
            return
        if selection_active:
            delete_selected_text()
        elif cursor_x > 0:
            text_buffer[cursor_y] = line[: cursor_x - 1] + line[cursor_x:]
            cursor_x -= 1
        elif cursor_y > 0:
            prev_len = len(text_buffer[cursor_y - 1])
            text_buffer[cursor_y - 1] += line
            text_buffer.pop(cursor_y)
            cursor_y -= 1
            cursor_x = prev_len
    elif event.key == pygame.K_DELETE:
        if file_read_only:
            print(f"Cannot edit: {current_file} is read-only")
            return
        if selection_active:
            delete_selected_text()
        elif cursor_x < len(line):
            text_buffer[cursor_y] = line[:cursor_x] + line[cursor_x + 1 :]
        elif cursor_y < len(text_buffer) - 1:
            text_buffer[cursor_y] += text_buffer[cursor_y + 1]
            text_buffer.pop(cursor_y + 1)
    elif event.key == pygame.K_RETURN:
        if file_read_only:
            print(f"Cannot edit: {current_file} is read-only")
            return
        if selection_active:
            delete_selected_text()
            line = text_buffer[cursor_y]
        text_buffer.insert(cursor_y + 1, line[cursor_x:])
        text_buffer[cursor_y] = line[:cursor_x]
        cursor_y += 1
        cursor_x = 0
    elif event.key == pygame.K_LEFT:
        if cursor_x > 0:
            cursor_x -= 1
        elif cursor_y > 0:
            cursor_y -= 1
            cursor_x = len(text_buffer[cursor_y])
    elif event.key == pygame.K_RIGHT:
        if cursor_x < len(line):
            cursor_x += 1
        elif cursor_y < len(text_buffer) - 1:
            cursor_y += 1
            cursor_x = 0
    elif event.key == pygame.K_UP:
        if cursor_y > 0:
            cursor_y -= 1
            cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.key == pygame.K_DOWN:
        if cursor_y < len(text_buffer) - 1:
            cursor_y += 1
            cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.key == pygame.K_HOME:
        cursor_x = 0
    elif event.key == pygame.K_END:
        cursor_x = len(text_buffer[cursor_y])
    elif event.key == pygame.K_PAGEUP:
        # Page up - move cursor up by visible page size
        max_visible_lines = get_editor_max_visible_lines()
        page_size = max(1, max_visible_lines - 1)  # Leave one line overlap
        cursor_y = max(0, cursor_y - page_size)
        cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.key == pygame.K_PAGEDOWN:
        # Page down - move cursor down by visible page size
        max_visible_lines = get_editor_max_visible_lines()
        page_size = max(1, max_visible_lines - 1)  # Leave one line overlap
        cursor_y = min(len(text_buffer) - 1, cursor_y + page_size)
        cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.unicode.isprintable():
        if file_read_only:
            print(f"Cannot edit: {current_file} is read-only")
            return
        if selection_active:
            delete_selected_text()
            line = text_buffer[cursor_y]
        text_buffer[cursor_y] = line[:cursor_x] + event.unicode + line[cursor_x:]
        cursor_x += 1

    # Update selection if Shift is pressed
    if shift_pressed and selection_active:
        update_selection(cursor_x, cursor_y)
    elif not shift_pressed:
        # Clear selection if Shift is not pressed and cursor moved
        if (cursor_x != old_cursor_x or cursor_y != old_cursor_y) and selection_active:
            clear_selection()
    
    # Ensure cursor is visible after any movement
    if cursor_x != old_cursor_x or cursor_y != old_cursor_y:
        ensure_cursor_visible()


def process_key_event(event):
    """Process a key event (either real or synthetic from repeat)"""
    global running, boot_index, boot_done, active_menu

    if not boot_done:
        # During boot sequence, allow skipping with Enter or Escape
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            # Skip to end of boot sequence
            boot_index = len(boot_lines)
            boot_done = True
    elif boot_done:
        # Handle email modal first (if open)
        if show_email_modal:
            # Handle scrolling in modal with arrow keys
            if event.key == pygame.K_UP:
                scroll_email_modal("up")
                return
            elif event.key == pygame.K_DOWN:
                scroll_email_modal("down")
                return
            elif event.key == pygame.K_PAGEUP:
                scroll_email_modal("up", email_modal_max_visible_lines // 2)
                return
            elif event.key == pygame.K_PAGEDOWN:
                scroll_email_modal("down", email_modal_max_visible_lines // 2)
                return
            elif event.key == pygame.K_HOME:
                email_modal_scroll_offset = 0
                return
            elif event.key == pygame.K_END:
                max_scroll = max(
                    0, len(email_modal_content_lines) - email_modal_max_visible_lines
                )
                email_modal_scroll_offset = max_scroll
                return
            else:
                # Any other key closes the modal
                close_email_modal()
                return

        # Check for Alt+F4 or Escape to exit
        keys = pygame.key.get_pressed()
        if (
            event.key == pygame.K_F4 and keys[pygame.K_LALT]
        ) or event.key == pygame.K_ESCAPE:
            running = False
        elif event.key >= pygame.K_F1 and event.key <= pygame.K_F12:
            fkey_num = event.key - pygame.K_F1 + 1

            if active_menu:
                # If menu is open, use F-keys to select menu items
                menu_items = menus[active_menu]
                if fkey_num <= len(menu_items):
                    if not handle_menu_action(active_menu, fkey_num - 1):
                        running = False  # Exit was selected
                    active_menu = None  # Close menu after selection
            else:
                # If no menu is open, open the corresponding menu (only F1-F3)
                if fkey_num <= 3:
                    active_menu = f"F{fkey_num}"
        elif event.key == pygame.K_TAB:
            # Tab key cycles through panels
            panels = ["editor", "files", "inbox"]
            current_idx = panels.index(active_panel)
            next_idx = (current_idx + 1) % len(panels)
            switch_panel(panels[next_idx])
        elif active_panel in ("files", "inbox"):
            # Navigate within side panels
            handle_panel_navigation(event)
        else:
            active_menu = None
            if active_panel == "editor":
                handle_text_input(event)


def main():
    global boot_index, boot_done, boot_timer, active_menu, running
    running = True

    # Initialize workspace and try to load current level file
    ensure_workspace_dir()
    if not load_file():  # Try to load the current level file
        # If file doesn't exist, create it with default content
        print(f"Creating new file: {current_file}")
    while running:
        dt = clock.tick(30) / 1000.0

        # Process regular events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Handle the key press and start tracking for repeats
                processed_event = handle_key_press(event.key, event)
                process_key_event(processed_event)

        # Check for key repeats (only when boot is done and no menus are active)
        if boot_done and not active_menu:
            repeat_key = update_key_repeat()
            if repeat_key:
                # Generate synthetic repeat event
                repeat_event = handle_key_press(repeat_key)
                if repeat_event:
                    process_key_event(repeat_event)

        if not boot_done:
            boot_timer += dt
            if boot_timer >= boot_speed and boot_index < len(boot_lines):
                boot_index += 1
                boot_timer = 0
            elif boot_index >= len(boot_lines):
                pygame.time.wait(500)
                boot_done = True
            draw_boot_screen()
        else:
            # Update file list and load emails on first run
            scan_workspace_files()
            if not emails:  # Load emails only once
                load_emails_for_level(current_level)
            draw_workspace()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
