import pygame, sys, time, random

pygame.init()
pygame.mixer.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro PC Boot - Text Editor")

FONT = pygame.font.Font(pygame.font.match_font("couriernew", bold=True), 18)
BIGFONT = pygame.font.Font(pygame.font.match_font("couriernew", bold=True), 22)
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
MENU_BG = (0, 60, 0)

boot_lines = [
    "JackROM BIOS 4.0 Release A4",
    "Copyright (C) 1985-1992 Jack Games Ltd.",
    "",
    "Memory Test: 640K OK",
    "Detecting IDE Devices ...",
    "Primary Master: 40MB ST-251",
    "Primary Slave: None",
    "Starting DOS...",
    "",
    "C:\\>bitworks.exe",
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


def draw_boot_screen():
    screen.fill(BLACK)
    for i in range(boot_index):
        line = boot_lines[i]
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (20, 40 + i * 24))
    pygame.display.flip()


def draw_editor():
    screen.fill(BLACK)
    # Draw menu bar
    pygame.draw.rect(screen, MENU_BG, (0, 0, WIDTH, 30))
    fkeys = ["F1-File", "F2-Edit", "F3-Help"]
    x = 10
    for label in fkeys:
        txt = FONT.render(label, True, GREEN)
        screen.blit(txt, (x, 5))
        x += 150

    # Draw menus if active
    if active_menu:
        menu_items = menus[active_menu]
        idx = ["F1", "F2", "F3"].index(active_menu)
        x = 10 + 150 * idx
        y = 30
        for item in menu_items:
            pygame.draw.rect(screen, GRAY, (x, y, 120, 25))
            t = FONT.render(item, True, GREEN)
            screen.blit(t, (x + 5, y + 3))
            y += 25

    # Draw text area
    yoff = 40
    for y, line in enumerate(text_buffer):
        text = FONT.render(line, True, GREEN)
        screen.blit(text, (20, yoff + y * 22))

    # Cursor blink
    global cursor_timer, cursor_visible
    cursor_timer += clock.get_time()
    if cursor_timer > 500:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    if cursor_visible:
        cx = 20 + FONT.size(text_buffer[cursor_y][:cursor_x])[0]
        cy = yoff + cursor_y * 22
        pygame.draw.rect(screen, GREEN, (cx, cy, 10, 18), 1)

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
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_F1, pygame.K_F2, pygame.K_F3):
                        active_menu = f"F{event.key - pygame.K_F1 + 1}"
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
