import pygame
import random
import win32com.client as win32
import math
import os
import json
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename, askopenfilename

# Initialize Pygame
pygame.init()

# Get screen dimensions
info = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = info.current_w, info.current_h

# Create fullscreen window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Grid2D")

# Cell size
cell_size = 16

# Calculate grid rows and columns
rows = (WINDOW_HEIGHT // cell_size) * 2
cols = (WINDOW_WIDTH // cell_size) * 2

# Initialize grid
grid = [[random.randint(0, 0) for _ in range(cols)] for _ in range(rows)]

# Define colors
WHITE = (255, 255, 255)
LIGHT_GRAY = (220, 220, 220)
DARK_GREEN = (0, 180, 0)
BUTTON_COLOR = (120, 120, 120)
HOVER_COLOR = (180, 180, 180)
TEXT_COLOR = (40, 40, 40)
ERASER_COLOR = (255, 100, 100)
ERASER_HOVER = (255, 150, 150)

# Camera offset
camera_x, camera_y = 0, 0

# Button class with improved visibility
class Button:
    def __init__(self, x, y, width, height, text, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color if color else BUTTON_COLOR
        self.hover_color = hover_color if hover_color else HOVER_COLOR
        self.is_hovered = False
        self.font = pygame.font.Font(None, 24)
        self.original_y = y
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        
        # Draw button with rounded corners
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)  # Border
        
        # Draw text
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

# Save grid to file
def save_grid(grid_data):
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = asksaveasfilename(defaultextension=".g2d", 
                                 filetypes=[("Grid2D Files", "*.g2d"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, 'w') as f:
            json.dump(grid_data, f)

# Load grid from file
def load_grid():
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = askopenfilename(filetypes=[("Grid2D Files", "*.g2d"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

# Create buttons with better layout
button_width, button_height = 100, 40
button_margin = 20
buttons = []

# Calculate total width needed for buttons
total_buttons_width = 5 * button_width + 4 * button_margin
start_x = (WINDOW_WIDTH - total_buttons_width) // 2

# Create buttons in a centered row at the bottom
button_y = WINDOW_HEIGHT - button_height - 20
buttons.append(Button(start_x, button_y, button_width, button_height, "Draw"))
buttons.append(Button(start_x + button_width + button_margin, button_y, button_width, button_height, "Erase", ERASER_COLOR, ERASER_HOVER))
buttons.append(Button(start_x + 2*(button_width + button_margin), button_y, button_width, button_height, "Save"))
buttons.append(Button(start_x + 3*(button_width + button_margin), button_y, button_width, button_height, "Load"))
buttons.append(Button(start_x + 4*(button_width + button_margin), button_y, button_width, button_height, "Exit"))

# Main game loop
running = True
drawing = False
erasing = False
clock = pygame.time.Clock()

while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()

    # Handle camera movement
    if mouse_pos[0] < 50:
        camera_x = max(camera_x - 1, 0)
    if mouse_pos[0] > WINDOW_WIDTH - 50:
        camera_x = min(camera_x + 1, cols - WINDOW_WIDTH // cell_size)
    if mouse_pos[1] < 50:
        camera_y = max(camera_y - 1, 0)
    if mouse_pos[1] > WINDOW_HEIGHT - 50:
        camera_y = min(camera_y + 1, rows - WINDOW_HEIGHT // cell_size)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                for button in buttons:
                    button.check_hover(mouse_pos)
                    if button.is_hovered:
                        if button.text == "Draw":
                            drawing = True
                            erasing = False
                        elif button.text == "Erase":
                            erasing = True
                            drawing = False
                        elif button.text == "Save":
                            save_grid(grid)
                        elif button.text == "Load":
                            loaded_grid = load_grid()
                            if loaded_grid:
                                grid = loaded_grid
                        elif button.text == "Exit":
                            running = False

    # Fill background with white
    screen.fill(WHITE)

    # Draw grid lines
    for i in range(0, WINDOW_HEIGHT, cell_size):
        pygame.draw.line(screen, LIGHT_GRAY, (0, i), (WINDOW_WIDTH, i), 1)
    for j in range(0, WINDOW_WIDTH, cell_size):
        pygame.draw.line(screen, LIGHT_GRAY, (j, 0), (j, WINDOW_HEIGHT), 1)

    # Draw grid cells with correct camera offset
    start_col = max(0, camera_x)
    end_col = min(cols, camera_x + WINDOW_WIDTH // cell_size + 1)
    start_row = max(0, camera_y)
    end_row = min(rows, camera_y + WINDOW_HEIGHT // cell_size + 1)

    for i in range(start_row, end_row):
        for j in range(start_col, end_col):
            if grid[i][j] == 1:
                pygame.draw.rect(screen, DARK_GREEN,
                               ((j - camera_x) * cell_size,
                                (i - camera_y) * cell_size,
                                cell_size, cell_size))

    # Handle drawing and erasing
    if mouse_buttons[0]:  # Left mouse button pressed
        # Only draw/erase if not hovering over buttons
        if not any(button.rect.collidepoint(mouse_pos) for button in buttons):
            col = (mouse_pos[0] // cell_size) + camera_x
            row = (mouse_pos[1] // cell_size) + camera_y
            
            if 0 <= row < rows and 0 <= col < cols:
                if drawing:
                    grid[row][col] = 1
                elif erasing:
                    grid[row][col] = 0

    # Draw buttons
    for button in buttons:
        button.check_hover(mouse_pos)
        button.draw(screen)

    # Update display
    pygame.display.flip()

    # Control frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()