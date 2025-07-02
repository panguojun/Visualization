import pygame
import random
import win32com.client as win32
import math
import os
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename, askopenfilename

# 初始化 Pygame
pygame.init()

# 设置窗口大小
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Grid2D")

# 方格大小
cell_size = 16

# 计算网格的行数和列数
rows = (WINDOW_HEIGHT // cell_size) * 2
cols = (WINDOW_WIDTH // cell_size) * 2

# 初始化网格
grid = [[random.randint(0, 0) for _ in range(cols)] for _ in range(rows)]

# 定义颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WHITE2 = (255, 200, 55)
DARK_GOLD = (80, 60, 0)
DARK_GREEN = (0, 180, 0)
BUTTON_COLOR = (50, 50, 50)

# 摄像机偏移量
camera_x, camera_y = 0, 0

# 按钮类
class Button:
    def __init__(self, x, y, radius, text):
        self.x = x
        self.y = y
        self.radius = radius
        self.original_radius = radius
        self.text = text
        self.original_y = y
        self.is_hovered = False
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        if self.is_hovered:
            current_radius = int(self.original_radius * 1.2)
            current_y = self.original_y - 10
        else:
            current_radius = self.original_radius
            current_y = self.original_y

        # 绘制柔和的白色轮廓线
        for i in range(3):
            pygame.draw.circle(screen, WHITE2, (self.x, current_y), current_radius + i, 1)

        pygame.draw.circle(screen, BUTTON_COLOR, (self.x, current_y), current_radius)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x, current_y))
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        x, y = mouse_pos
        distance = ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
        self.is_hovered = distance <= self.original_radius

# 计算相邻细胞的数量
def count_neighbors(grid, x, y):
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            nx, ny = x + i, y + j
            if 0 <= nx < rows and 0 <= ny < cols:
                count += grid[nx][ny]
    return count

# 更新网格状态
def update_grid(grid):
    new_grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            neighbors = count_neighbors(grid, i, j)
            if grid[i][j] == 1 and (neighbors == 2 or neighbors == 3):
                new_grid[i][j] = 1
            elif grid[i][j] == 0 and neighbors == 3:
                new_grid[i][j] = 1
            else:
                new_grid[i][j] = 0
    return new_grid

# Bresenham 线段光栅化算法
def bresenham_line(x1, y1, x2, y2):
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    return points

def rasterize_circle(center_x, center_y, radius):
    points = []
    x = 0
    y = radius
    d = 3 - 2 * radius
    while x <= y:
        points.extend([
            (center_x + x, center_y + y), (center_x - x, center_y + y),
            (center_x + x, center_y - y), (center_x - x, center_y - y),
            (center_x + y, center_y + x), (center_x - y, center_y + x),
            (center_x + y, center_y - x), (center_x - y, center_y - x)
        ])
        if d < 0:
            d = d + 4 * x + 6
        else:
            d = d + 4 * (x - y) + 10
            y = y - 1
        x = x + 1
    return points

def rasterize_rectangle(x1, y1, x2, y2):
    points = []
    # 上边
    for x in range(x1, x2 + 1):
        points.append((x, y1))
    # 下边
    for x in range(x1, x2 + 1):
        points.append((x, y2))
    # 左边
    for y in range(y1, y2 + 1):
        points.append((x1, y))
    # 右边
    for y in range(y1, y2 + 1):
        points.append((x2, y))
    return points

def rasterize_arc(center_x, center_y, radius, start_angle, end_angle):
    points = []
    start_angle = math.radians(start_angle)
    end_angle = math.radians(end_angle)
    angle = start_angle
    while angle <= end_angle:
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        points.append((x, y))
        angle += 0.01  # 步长可以根据需要调整
    return points

def readCAD():
    print("readCAD")
    try:
        # 连接到 AutoCAD
        acad = win32.GetActiveObject("AutoCAD.Application")
        print("成功连接到 AutoCAD。")

        # 获取当前活动文档
        doc = acad.ActiveDocument
        print(f"当前活动文档名称: {doc.Name}")
        # 获取 AutoCAD 中的所有对象
        entities = []
        for entity in doc.ModelSpace:
            print(f"entity.EntityName={entity.EntityName}")
            entities.append(entity)

        # 处理不同类型的实体
        for entity in entities:
            if entity.EntityName == "AcDbLine":
                start_point = entity.StartPoint
                end_point = entity.EndPoint
                x1, y1 = int(start_point[0] // cell_size), int(start_point[1] // cell_size)
                x2, y2 = int(end_point[0] // cell_size), int(end_point[1] // cell_size)
                rasterized_points = bresenham_line(x1, y1, x2, y2)
            elif entity.EntityName == "AcDbCircle":
                center = entity.Center
                radius = entity.Radius
                center_x, center_y = int(center[0] // cell_size), int(center[1] // cell_size)
                radius = int(radius // cell_size)
                rasterized_points = rasterize_circle(center_x, center_y, radius)
            elif entity.EntityName == "AcDbArc":
                center = entity.Center
                radius = entity.Radius
                start_angle = entity.StartAngle
                end_angle = entity.EndAngle
                center_x, center_y = int(center[0] // cell_size), int(center[1] // cell_size)
                radius = int(radius // cell_size)
                rasterized_points = rasterize_arc(center_x, center_y, radius, start_angle, end_angle)
            elif entity.EntityName == "AcDbPolyline":
                # 假设方形是一个封闭的 4 点多段线
                if entity.Closed:
                    min_x, min_y = float('inf'), float('inf')
                    max_x, max_y = float('-inf'), float('-inf')
                    coordinates = entity.Coordinates
                    num_vertices = len(coordinates) // 2  # 每个顶点有 x 和 y 两个坐标

                    for i in range(num_vertices):
                        x = coordinates[i]
                        y = coordinates[i + 1]
                        x = int(x // cell_size)
                        y = int(y // cell_size)
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                    rasterized_points = rasterize_rectangle(min_x, min_y, max_x, max_y)
                else:
                    continue
            else:
                continue
            # 将光栅化的点应用到网格中
            for point in rasterized_points:
                x, y = point
                if 0 <= x < cols and 0 <= y < rows:
                    grid[y][x] = 1
    except Exception as e:
        print(f"连接 AutoCAD 时出错: {e}")
    return grid

# 保存网格数据到 .g2 文件
def save_grid(grid):
    root = Tk()
    root.withdraw()
    file_path = asksaveasfilename(defaultextension=".g2", filetypes=[("Grid2D Files", "*.g2")])
    if file_path:
        with open(file_path, 'w') as file:
            import json
            json.dump(grid, file)

# 从 .g2 文件读取网格数据
def load_grid():
    root = Tk()
    root.withdraw()
    file_path = askopenfilename(filetypes=[("Grid2D Files", "*.g2")])
    if file_path:
        with open(file_path, 'r') as file:
            import json
            return json.load(file)
    return None

# 创建按钮
button_radius = 30
buttons_bottom = []

# 底部按钮
button_x_offset = 20
for j in range(4):
    x = j * (button_radius * 2 + button_x_offset) + button_radius + 10
    y = WINDOW_HEIGHT - button_radius - 10
    if j == 0:
        drawbutton = Button(x, y, button_radius * 1.1, "Draw")
    elif j == 1:
        save_button = Button(x, y, button_radius * 1.1, "Save")
        buttons_bottom.append(save_button)
    elif j == 2:
        load_button = Button(x, y, button_radius * 1.1, "Load")
        buttons_bottom.append(load_button)
    elif j == 3:
        exitbutton = Button(x, y, button_radius * 1.1, "Exit")

# 主循环
running = True
drawing = False
clock = pygame.time.Clock()
update_scene = False
import_cad = False
left_button_pressed = False

while running:
    mouse_pos = pygame.mouse.get_pos()

    # 处理摄像机移动
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
            if event.button == 1:  # 1 代表鼠标左键
                left_button_pressed = True
            for button in buttons_bottom:
                if button.is_hovered:
                    if button.text == "Save":
                        save_grid(grid)
                    elif button.text == "Load":
                        loaded_grid = load_grid()
                        if loaded_grid:
                            grid = loaded_grid
                    elif button.text != "Load" and button.text != "Save":
                        update_scene = True
                        import_cad = True
            if exitbutton.is_hovered:
                running = False
            if drawbutton.is_hovered:
                drawing = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 1 代表鼠标左键
                left_button_pressed = False

    # 填充背景色
    screen.fill(BLACK)

    # 绘制网格线
    for i in range(rows + 1):
        pygame.draw.line(screen, DARK_GOLD, (0, i * cell_size),
                         (WINDOW_WIDTH, i * cell_size), 1)
    for j in range(cols + 1):
        pygame.draw.line(screen, DARK_GOLD, (j * cell_size, 0),
                         (j * cell_size, WINDOW_HEIGHT), 1)

    # 绘制网格
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 1:
                pygame.draw.rect(screen, DARK_GREEN,
                                 (j * cell_size - camera_x * cell_size,
                                  i * cell_size - camera_y * cell_size,
                                  cell_size, cell_size))

    # 更新按钮状态
    for button in buttons_bottom:
        button.check_hover(mouse_pos)
        button.draw(screen)

    exitbutton.check_hover(mouse_pos)
    exitbutton.draw(screen)

    drawbutton.check_hover(mouse_pos)
    drawbutton.draw(screen)

    # 处理绘图
    if drawing and left_button_pressed:
        # 将鼠标位置转换为网格坐标
        col = (mouse_pos[0] + camera_x * cell_size) // cell_size
        row = (mouse_pos[1] + camera_y * cell_size) // cell_size
        if 0 <= row < rows and 0 <= col < cols:
            grid[row][col] = 1

    # 导入 CAD 图形
    if import_cad:
        readCAD()
        import_cad = False

    # 更新显示
    pygame.display.flip()

    # 控制帧率，降低更新速度
    clock.tick(60)

# 退出 Pygame
pygame.quit()