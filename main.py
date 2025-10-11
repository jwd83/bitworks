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
BIGFONT = pygame.font.Font(pygame.font.match_font("couriernew", bold=True), big_font_size)
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

active_menu = None
menus = {
    "F1": ["New", "Open", "Save", "Exit"],
    "F2": ["Cut", "Copy", "Paste"],
    "F3": ["About"],
}

# Key repeat system
KEY_REPEAT_DELAY = 750  # 3/4 second initial delay (milliseconds)
KEY_REPEAT_INTERVAL = 250  # 1/4 second repeat interval (milliseconds)
key_states = {}  # Track key press states and timers
last_key_event = None  # Track the last processed key for repeats

# Keys that should repeat when held down
REPEAT_KEYS = {
    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
    pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_HOME, pygame.K_END,
    pygame.K_PAGEUP, pygame.K_PAGEDOWN
}

def should_key_repeat(key):
    """Check if a key should repeat when held down"""
    return key in REPEAT_KEYS or (key >= 32 and key <= 126)  # Include printable ASCII characters

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
        del text_buffer[start_y:end_y + 1]
        
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
        text_buffer.insert(cursor_y + len(clipboard_lines) - 1, clipboard_lines[-1] + after_cursor)
        
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
        time_held = current_time - key_data['start_time']
        
        if not key_data['repeating'] and time_held >= KEY_REPEAT_DELAY:
            # Start repeating
            key_data['repeating'] = True
            key_data['last_repeat'] = current_time
            return key  # Return the key to repeat
        elif key_data['repeating'] and (current_time - key_data['last_repeat']) >= KEY_REPEAT_INTERVAL:
            # Continue repeating
            key_data['last_repeat'] = current_time
            return key  # Return the key to repeat
    
    return None

def handle_key_press(key, event=None):
    """Handle a key press, either from event or repeat"""
    global key_states, last_key_event
    current_time = pygame.time.get_ticks()
    
    # If this is a new key press (not a repeat), track it if it should repeat
    if event and key not in key_states and should_key_repeat(key):
        key_states[key] = {
            'start_time': current_time,
            'repeating': False,
            'last_repeat': 0
        }
        last_key_event = event
    
    # Create a synthetic event for repeats
    if not event and last_key_event:
        # Create a synthetic event based on the last real event
        event = type('Event', (), {
            'type': pygame.KEYDOWN,
            'key': key,
            'unicode': last_key_event.unicode if hasattr(last_key_event, 'unicode') else '',
            'mod': last_key_event.mod if hasattr(last_key_event, 'mod') else 0
        })()
    
    return event

def handle_menu_action(menu, item_index):
    """Handle menu item selection"""
    global running
    
    if menu == "F1":
        menu_items = menus["F1"]
        if item_index < len(menu_items):
            action = menu_items[item_index]
            if action == "New":
                new_file()
                print("New file created")
            elif action == "Open":
                if load_file():
                    print("File loaded from workspace/1.v")
                else:
                    print("No file found at workspace/1.v")
            elif action == "Save":
                if save_file():
                    print("File saved to workspace/1.v")
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
            print(f"Help action: {action} (not yet implemented)")
        # Add Help menu actions here as needed
    
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
    skip_font = pygame.font.Font(pygame.font.match_font("couriernew"), max(12, font_size // 2))
    skip_surface = skip_font.render(skip_text, True, GREEN)
    skip_rect = skip_surface.get_rect()
    skip_rect.bottomright = (WIDTH - 10, HEIGHT - 10)
    screen.blit(skip_surface, skip_rect)
    
    pygame.display.flip()


def draw_editor():
    screen.fill(BLACK)
    
    # Scale UI elements based on screen size
    x_margin = WIDTH // 50  # Text margin from left
    menu_height = font_size + 14  # Menu bar height
    text_yoff = menu_height + 10  # Text area Y offset
    line_height = font_size + 4  # Line spacing
    menu_spacing = WIDTH // 8  # Space between menu items
    menu_item_height = font_size + 8  # Height of dropdown menu items
    menu_item_width = WIDTH // 8  # Width of dropdown menu items
    
    # Draw text area with selection highlighting
    bounds = get_selection_bounds() if selection_active else None
    
    for y, line in enumerate(text_buffer):
        line_y = text_yoff + y * line_height
        
        # Draw selection background if this line is selected
        if bounds:
            start_x, start_y, end_x, end_y = bounds
            if start_y <= y <= end_y:
                # Calculate selection bounds for this line
                if y == start_y and y == end_y:
                    # Single line selection
                    sel_start = x_margin + FONT.size(line[:start_x])[0] if line else x_margin
                    sel_end = x_margin + FONT.size(line[:end_x])[0] if line else x_margin
                elif y == start_y:
                    # Start of multi-line selection
                    sel_start = x_margin + FONT.size(line[:start_x])[0] if line else x_margin
                    sel_end = x_margin + FONT.size(line)[0] if line else x_margin
                elif y == end_y:
                    # End of multi-line selection
                    sel_start = x_margin
                    sel_end = x_margin + FONT.size(line[:end_x])[0] if line else x_margin
                else:
                    # Middle of multi-line selection
                    sel_start = x_margin
                    sel_end = x_margin + FONT.size(line)[0] if line else x_margin
                
                # Draw selection background
                sel_width = max(10, sel_end - sel_start)  # Minimum width for empty lines
                pygame.draw.rect(screen, SELECTION_BG, (sel_start, line_y, sel_width, line_height))
        
        # Draw text
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (x_margin, line_y))

    # Draw cursor
    global cursor_timer, cursor_visible
    cursor_timer += clock.get_time()
    if cursor_timer > 500:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    if cursor_visible:
        cx = x_margin + FONT.size(text_buffer[cursor_y][:cursor_x])[0]
        cy = text_yoff + cursor_y * line_height
        cursor_width = max(2, font_size // 9)
        pygame.draw.rect(screen, GREEN, (cx, cy, cursor_width * 5, font_size), 1)
    
    # Draw menu bar (top layer)
    pygame.draw.rect(screen, MENU_BG, (0, 0, WIDTH, menu_height))
    fkeys = ["F1-File", "F2-Edit", "F3-Help"]
    x = x_margin
    for label in fkeys:
        txt = FONT.render(label, True, GREEN)
        screen.blit(txt, (x, (menu_height - font_size) // 2))
        x += menu_spacing

    # Draw dropdown menus if active (top layer)
    if active_menu:
        menu_items = menus[active_menu]
        idx = ["F1", "F2", "F3"].index(active_menu)
        x = x_margin + menu_spacing * idx
        y = menu_height
        for i, item in enumerate(menu_items):
            pygame.draw.rect(screen, GRAY, (x, y, menu_item_width, menu_item_height))
            # Show F-key number before menu item
            fkey_text = f"F{i+1}-{item}"
            t = FONT.render(fkey_text, True, GREEN)
            screen.blit(t, (x + 8, y + (menu_item_height - font_size) // 2))
            y += menu_item_height
    
    # Draw status text in bottom-right corner
    status_text = "ESC or Alt+F4 to exit"
    status_font = pygame.font.Font(pygame.font.match_font("couriernew"), max(12, font_size // 2))
    status_surface = status_font.render(status_text, True, GREEN)
    status_rect = status_surface.get_rect()
    status_rect.bottomright = (WIDTH - 10, HEIGHT - 10)
    screen.blit(status_surface, status_rect)

    pygame.display.flip()


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
            text_buffer[cursor_y] = line[:cursor_x] + line[cursor_x + 1:]
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
                # If F-key is beyond menu items, don't close menu
            else:
                # If no menu is open, open the corresponding menu (only F1-F3)
                if fkey_num <= 3:
                    active_menu = f"F{fkey_num}"
        else:
            active_menu = None
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
            draw_editor()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
