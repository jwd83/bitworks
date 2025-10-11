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

active_menu = None
menus = {
    "F1": ["New", "Open", "Save", "Exit"],
    "F2": ["Cut", "Copy", "Paste"],
    "F3": ["About"],
}

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
            print(f"Edit action: {action} (not yet implemented)")
        # Add Edit menu actions here as needed
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
    
    # Draw text area first (background layer)
    for y, line in enumerate(text_buffer):
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (x_margin, text_yoff + y * line_height))

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

    if event.key == pygame.K_BACKSPACE:
        if cursor_x > 0:
            text_buffer[cursor_y] = line[: cursor_x - 1] + line[cursor_x:]
            cursor_x -= 1
        elif cursor_y > 0:
            prev_len = len(text_buffer[cursor_y - 1])
            text_buffer[cursor_y - 1] += line
            text_buffer.pop(cursor_y)
            cursor_y -= 1
            cursor_x = prev_len
    elif event.key == pygame.K_RETURN:
        text_buffer.insert(cursor_y + 1, line[cursor_x:])
        text_buffer[cursor_y] = line[:cursor_x]
        cursor_y += 1
        cursor_x = 0
    elif event.key == pygame.K_LEFT:
        cursor_x = max(0, cursor_x - 1)
    elif event.key == pygame.K_RIGHT:
        cursor_x = min(len(line), cursor_x + 1)
    elif event.key == pygame.K_UP:
        cursor_y = max(0, cursor_y - 1)
        cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.key == pygame.K_DOWN:
        cursor_y = min(len(text_buffer) - 1, cursor_y + 1)
        cursor_x = min(cursor_x, len(text_buffer[cursor_y]))
    elif event.unicode.isprintable():
        text_buffer[cursor_y] = line[:cursor_x] + event.unicode + line[cursor_x:]
        cursor_x += 1


def main():
    global boot_index, boot_done, boot_timer, active_menu
    running = True
    while running:
        dt = clock.tick(30) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif boot_done:
                if event.type == pygame.KEYDOWN:
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
