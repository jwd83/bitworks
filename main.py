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
cursor_visible = True
cursor_timer = 0
running = False

# Text selection system
selection_start_x, selection_start_y = None, None
selection_end_x, selection_end_y = None, None
selection_active = False
clipboard = ""  # Simple clipboard storage

# Workspace layout
LEFT_PANEL_WIDTH = WIDTH // 3  # Left third for browser and inbox
FILE_BROWSER_HEIGHT = HEIGHT // 2  # Top half of left panel
INBOX_HEIGHT = HEIGHT - FILE_BROWSER_HEIGHT  # Bottom half of left panel
EDITOR_WIDTH = WIDTH - LEFT_PANEL_WIDTH  # Right two-thirds for editor
EDITOR_X_OFFSET = LEFT_PANEL_WIDTH  # Editor starts after left panel

# File browser state
workspace_files = []
selected_file_index = 0
current_file = "1.v"  # Currently opened file

# Email inbox state
emails = [
    {"from": "system@bitworks", "subject": "Welcome to BitWorks IDE", "read": False},
    {"from": "compiler@bitworks", "subject": "Synthesis Report Available", "read": True},
    {"from": "debugger@bitworks", "subject": "Waveform Analysis Complete", "read": False},
]
selected_email_index = 0
active_panel = "editor"  # "editor", "files", "inbox"

active_menu = None
menus = {
    "F1": ["New File", "Open File", "Save File", "Exit"],
    "F2": ["Cut", "Copy", "Paste"],
    "F3": ["Files Panel", "Inbox Panel", "Editor Panel"],  # Panel navigation
}

# Key repeat system
KEY_REPEAT_DELAY = 750  # 3/4 second initial delay (milliseconds)
KEY_REPEAT_INTERVAL = 250  # 1/4 second repeat interval (milliseconds)
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
def ensure_workspace_dir():
    """Create workspace directory if it doesn't exist"""
    if not os.path.exists("workspace"):
        os.makedirs("workspace")


def save_file():
    """Save current text buffer to workspace/1.v"""
    try:
        ensure_workspace_dir()
        with open("workspace/1.v", "w", encoding="utf-8") as f:
            f.write("\n".join(text_buffer))
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False


def load_file():
    """Load text from workspace/1.v if it exists"""
    global text_buffer, cursor_x, cursor_y
    try:
        if os.path.exists("workspace/1.v"):
            with open("workspace/1.v", "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    text_buffer = content.split("\n")
                else:
                    text_buffer = [""]
                cursor_x, cursor_y = 0, 0
                return True
        return False
    except Exception as e:
        print(f"Error loading file: {e}")
        return False


def new_file():
    """Clear the text buffer for a new file"""
    global text_buffer, cursor_x, cursor_y
    text_buffer = [""]
    cursor_x, cursor_y = 0, 0
    clear_selection()

def scan_workspace_files():
    """Scan workspace directory for .v and .s files"""
    global workspace_files
    workspace_files = []
    
    try:
        ensure_workspace_dir()
        if os.path.exists("workspace"):
            for filename in sorted(os.listdir("workspace")):
                if filename.endswith(('.v', '.s')):
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
    global text_buffer, cursor_x, cursor_y, current_file
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
                current_file = filename
                clear_selection()
                print(f"Loaded file: {filename}")
                return True
        else:
            print(f"File not found: {filename}")
            return False
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        return False

def save_current_file():
    """Save current text buffer to the current file"""
    global current_file
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

def switch_panel(panel_name):
    """Switch to a different panel"""
    global active_panel
    if panel_name in ["editor", "files", "inbox"]:
        active_panel = panel_name
        print(f"Switched to {panel_name} panel")
        return True
    return False

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
                emails[selected_email_index]["read"] = True
                print(f"Opened email: {emails[selected_email_index]['subject']}")


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
                if not cut_to_clipboard():
                    print("Nothing to cut (no selection)")
            elif action == "Copy":
                if not copy_to_clipboard():
                    print("Nothing to copy (no selection)")
            elif action == "Paste":
                if not paste_from_clipboard():
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
        pygame.font.match_font("couriernew"), max(12, font_size // 2)
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
    small_font_size = max(12, font_size // 2)
    small_font = pygame.font.Font(pygame.font.match_font("couriernew"), small_font_size)
    
    # Draw menu bar across full width
    draw_menu_bar(menu_height)
    
    # Draw vertical separator lines
    pygame.draw.line(screen, GREEN, (LEFT_PANEL_WIDTH, menu_height), (LEFT_PANEL_WIDTH, HEIGHT), 1)
    pygame.draw.line(screen, GREEN, (0, FILE_BROWSER_HEIGHT), (LEFT_PANEL_WIDTH, FILE_BROWSER_HEIGHT), 1)
    
    # Draw file browser (top-left)
    draw_file_browser(menu_height, FILE_BROWSER_HEIGHT, line_height, small_font)
    
    # Draw email inbox (bottom-left)
    draw_email_inbox(FILE_BROWSER_HEIGHT, HEIGHT, line_height, small_font)
    
    # Draw text editor (right two-thirds)
    draw_text_editor(EDITOR_X_OFFSET, menu_height, EDITOR_WIDTH, HEIGHT - menu_height, line_height)
    
    # Draw status text in bottom-right corner
    status_text = f"File: {current_file} | Panel: {active_panel.title()}"
    status_surface = small_font.render(status_text, True, GREEN)
    status_rect = status_surface.get_rect()
    status_rect.bottomright = (WIDTH - 10, HEIGHT - 10)
    screen.blit(status_surface, status_rect)
    
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
    
    # Draw dropdown menus if active
    if active_menu:
        draw_dropdown_menu(menu_height, x_margin, menu_spacing)

def draw_dropdown_menu(menu_height, x_margin, menu_spacing):
    """Draw dropdown menu"""
    menu_items = menus[active_menu]
    idx = ["F1", "F2", "F3"].index(active_menu)
    x = x_margin + menu_spacing * idx
    y = menu_height
    menu_item_height = font_size + 8
    menu_item_width = WIDTH // 8
    
    for i, item in enumerate(menu_items):
        pygame.draw.rect(screen, GRAY, (x, y, menu_item_width, menu_item_height))
        fkey_text = f"F{i+1}-{item}"
        t = FONT.render(fkey_text, True, GREEN)
        screen.blit(t, (x + 8, y + (menu_item_height - font_size) // 2))
        y += menu_item_height

def draw_file_browser(y_start, y_end, line_height, small_font):
    """Draw the file browser panel"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "files" else GRAY
    pygame.draw.rect(screen, header_bg, (0, y_start, LEFT_PANEL_WIDTH, header_height))
    
    header_text = small_font.render("FILES (.v/.s)", True, GREEN)
    screen.blit(header_text, (5, y_start + 2))
    
    # File list
    y = y_start + header_height + 5
    max_files = (FILE_BROWSER_HEIGHT - header_height - 10) // line_height
    
    for i, filename in enumerate(workspace_files[:max_files]):
        if i == selected_file_index and active_panel == "files":
            # Highlight selected file
            pygame.draw.rect(screen, SELECTION_BG, (2, y - 2, LEFT_PANEL_WIDTH - 4, line_height))
        
        # Show file type icon
        icon = "V" if filename.endswith('.v') else "S"
        icon_text = small_font.render(f"[{icon}]", True, GREEN)
        screen.blit(icon_text, (5, y))
        
        # Show filename (truncate if too long)
        max_name_width = LEFT_PANEL_WIDTH - 35
        name_text = filename
        if small_font.size(name_text)[0] > max_name_width:
            while small_font.size(name_text + "...")[0] > max_name_width and len(name_text) > 0:
                name_text = name_text[:-1]
            name_text += "..."
        
        file_text = small_font.render(name_text, True, GREEN)
        screen.blit(file_text, (30, y))
        
        # Mark current file
        if filename == current_file:
            current_marker = small_font.render("*", True, GREEN)
            screen.blit(current_marker, (LEFT_PANEL_WIDTH - 15, y))
        
        y += line_height

def draw_email_inbox(y_start, y_end, line_height, small_font):
    """Draw the email inbox panel"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "inbox" else GRAY
    pygame.draw.rect(screen, header_bg, (0, y_start, LEFT_PANEL_WIDTH, header_height))
    
    header_text = small_font.render("INBOX", True, GREEN)
    screen.blit(header_text, (5, y_start + 2))
    
    # Email list
    y = y_start + header_height + 5
    max_emails = (INBOX_HEIGHT - header_height - 10) // line_height
    
    for i, email in enumerate(emails[:max_emails]):
        if i == selected_email_index and active_panel == "inbox":
            # Highlight selected email
            pygame.draw.rect(screen, SELECTION_BG, (2, y - 2, LEFT_PANEL_WIDTH - 4, line_height))
        
        # Show read/unread status
        status = " " if email["read"] else "●"
        status_text = small_font.render(status, True, GREEN)
        screen.blit(status_text, (5, y))
        
        # Show subject (truncate if too long)
        max_subject_width = LEFT_PANEL_WIDTH - 25
        subject = email["subject"]
        if small_font.size(subject)[0] > max_subject_width:
            while small_font.size(subject + "...")[0] > max_subject_width and len(subject) > 0:
                subject = subject[:-1]
            subject += "..."
        
        subject_text = small_font.render(subject, True, GREEN)
        screen.blit(subject_text, (15, y))
        
        y += line_height

def draw_text_editor(x_start, y_start, width, height, line_height):
    """Draw the text editor panel"""
    # Panel header
    header_height = line_height + 4
    header_bg = MENU_BG if active_panel == "editor" else GRAY
    pygame.draw.rect(screen, header_bg, (x_start, y_start, width, header_height))
    
    small_font = pygame.font.Font(pygame.font.match_font("couriernew"), max(12, font_size // 2))
    header_text = small_font.render(f"EDITOR - {current_file}", True, GREEN)
    screen.blit(header_text, (x_start + 5, y_start + 2))
    
    # Text area
    text_y_start = y_start + header_height + 5
    text_x_margin = x_start + 10
    max_lines = (height - header_height - 10) // line_height
    
    # Draw text with selection highlighting (only if editor is active)
    bounds = get_selection_bounds() if selection_active and active_panel == "editor" else None
    
    for y, line in enumerate(text_buffer[:max_lines]):
        line_y = text_y_start + y * line_height
        
        # Draw selection background if this line is selected
        if bounds:
            start_x, start_y, end_x, end_y = bounds
            if start_y <= y <= end_y:
                # Calculate selection bounds for this line
                if y == start_y and y == end_y:
                    sel_start = text_x_margin + FONT.size(line[:start_x])[0] if line else text_x_margin
                    sel_end = text_x_margin + FONT.size(line[:end_x])[0] if line else text_x_margin
                elif y == start_y:
                    sel_start = text_x_margin + FONT.size(line[:start_x])[0] if line else text_x_margin
                    sel_end = text_x_margin + FONT.size(line)[0] if line else text_x_margin
                elif y == end_y:
                    sel_start = text_x_margin
                    sel_end = text_x_margin + FONT.size(line[:end_x])[0] if line else text_x_margin
                else:
                    sel_start = text_x_margin
                    sel_end = text_x_margin + FONT.size(line)[0] if line else text_x_margin
                
                sel_width = max(10, sel_end - sel_start)
                pygame.draw.rect(screen, SELECTION_BG, (sel_start, line_y, sel_width, line_height))
        
        # Draw text
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (text_x_margin, line_y))
    
    # Draw cursor (only if editor is active)
    if active_panel == "editor":
        draw_cursor(text_x_margin, text_y_start, line_height)

def draw_cursor(text_x_margin, text_y_start, line_height):
    """Draw the text cursor"""
    global cursor_timer, cursor_visible
    cursor_timer += clock.get_time()
    if cursor_timer > 500:
        cursor_visible = not cursor_visible
        cursor_timer = 0
    
    if cursor_visible and cursor_y < len(text_buffer):
        cx = text_x_margin + FONT.size(text_buffer[cursor_y][:cursor_x])[0]
        cy = text_y_start + cursor_y * line_height
        cursor_width = max(2, font_size // 9)
        pygame.draw.rect(screen, GREEN, (cx, cy, cursor_width * 5, font_size), 1)


def handle_text_input(event):
    global cursor_x, cursor_y
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
            cut_to_clipboard()
            return
        elif event.key == pygame.K_v:
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
        if selection_active:
            delete_selected_text()
        elif cursor_x < len(line):
            text_buffer[cursor_y] = line[:cursor_x] + line[cursor_x + 1 :]
        elif cursor_y < len(text_buffer) - 1:
            text_buffer[cursor_y] += text_buffer[cursor_y + 1]
            text_buffer.pop(cursor_y + 1)
    elif event.key == pygame.K_RETURN:
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
    elif event.unicode.isprintable():
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
        # Check for Alt+F4 or Escape to exit
        keys = pygame.key.get_pressed()
        if (event.key == pygame.K_F4 and keys[pygame.K_LALT]) or event.key == pygame.K_ESCAPE:
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
            # Update file list periodically or on demand
            scan_workspace_files()
            draw_workspace()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
