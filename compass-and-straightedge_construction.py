import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Set up fullscreen display
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Geometric Construction Tool")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (220, 220, 220)  # 浅灰色背景格线
LIGHT_BLUE = (173, 216, 230)
GRID_COLOR = (230, 230, 230)  # 更浅的格线颜色

# Tool types
TOOL_STRAIGHTEDGE = 0
TOOL_COMPASS = 1

# Global variables
current_tool = TOOL_STRAIGHTEDGE
points = []  # Stores all points
lines = []  # Stores all line segments (point1, point2)
circles = []  # Stores all circles (center, radius)
intersections = []  # Stores all intersection points
temp_circle = None  # Temporary circle being drawn
temp_line = None  # Temporary line being drawn
snap_distance = 15  # Pixel distance for snapping
grid_size = 20  # Grid spacing

# Button settings
button_font = pygame.font.SysFont('Arial', 20)
straightedge_button = pygame.Rect(20, 20, 120, 40)
compass_button = pygame.Rect(160, 20, 120, 40)

def distance(p1, p2):
    """Calculate distance between two points"""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def line_intersection(line1, line2):
    """Find intersection point of two line segments"""
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2
    
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:  # Parallel or coincident
        return None
    
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    
    if 0 <= ua <= 1 and 0 <= ub <= 1:  # Segments intersect
        x = x1 + ua * (x2 - x1)
        y = y1 + ua * (y2 - y1)
        return (x, y)
    return None

def circle_line_intersection(circle, line):
    """Find intersections between circle and line segment"""
    (cx, cy), r = circle
    (x1, y1), (x2, y2) = line
    
    # Convert line to general form: ax + by + c = 0
    a = y2 - y1
    b = x1 - x2
    c = x2 * y1 - x1 * y2
    
    # Calculate distance from center to line
    dist = abs(a * cx + b * cy + c) / math.sqrt(a**2 + b**2)
    
    if dist > r:  # No intersection
        return []
    
    # Calculate intersection points
    if b == 0:  # Vertical line
        x = -c / a
        term = math.sqrt(r**2 - (x - cx)**2)
        y1 = cy + term
        y2 = cy - term
        # Check if points are on the segment
        intersections = []
        if min(y1, y2) <= y1 <= max(y1, y2):
            intersections.append((x, y1))
        if min(y1, y2) <= y2 <= max(y1, y2):
            intersections.append((x, y2))
        return intersections
    else:
        m = -a / b
        k = -c / b
        A = 1 + m**2
        B = -2 * cx + 2 * m * (k - cy)
        C = cx**2 + (k - cy)**2 - r**2
        
        discriminant = B**2 - 4 * A * C
        if discriminant < 0:  # No intersection
            return []
        
        x1 = (-B + math.sqrt(discriminant)) / (2 * A)
        x2 = (-B - math.sqrt(discriminant)) / (2 * A)
        y1 = m * x1 + k
        y2 = m * x2 + k
        
        # Check if points are on the segment
        intersections = []
        if min(line[0][0], line[1][0]) <= x1 <= max(line[0][0], line[1][0]):
            intersections.append((x1, y1))
        if min(line[0][0], line[1][0]) <= x2 <= max(line[0][0], line[1][0]):
            intersections.append((x2, y2))
        return intersections

def circle_intersection(circle1, circle2):
    """Find intersections between two circles"""
    (x1, y1), r1 = circle1
    (x2, y2), r2 = circle2
    
    # Calculate distance between centers
    d = distance((x1, y1), (x2, y2))
    
    # Check if circles intersect
    if d > r1 + r2 or d < abs(r1 - r2):
        return []  # No intersection
    
    # Calculate intersection points
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(r1**2 - a**2)
    
    xm = x1 + a * (x2 - x1) / d
    ym = y1 + a * (y2 - y1) / d
    
    xs1 = xm + h * (y2 - y1) / d
    ys1 = ym - h * (x2 - x1) / d
    
    xs2 = xm - h * (y2 - y1) / d
    ys2 = ym + h * (x2 - x1) / d
    
    if xs1 == xs2 and ys1 == ys2:  # Tangent
        return [(xs1, ys1)]
    else:
        return [(xs1, ys1), (xs2, ys2)]

def find_all_intersections():
    """Find all intersections between geometric elements"""
    global intersections
    intersections = []
    
    # Line-line intersections
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            intersection = line_intersection(lines[i], lines[j])
            if intersection:
                intersections.append(intersection)
    
    # Circle-line intersections
    for circle in circles:
        for line in lines:
            points = circle_line_intersection(circle, line)
            intersections.extend(points)
    
    # Circle-circle intersections
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            points = circle_intersection(circles[i], circles[j])
            intersections.extend(points)

def snap_to_point(pos):
    """Snap to nearby points or intersections with visual feedback"""
    snap_target = None
    
    # Check intersections first
    for p in intersections:
        if distance(pos, p) < snap_distance:
            snap_target = p
            break
    
    # Check existing points if no intersection found
    if not snap_target:
        for line in lines:
            for p in line:
                if distance(pos, p) < snap_distance:
                    snap_target = p
                    break
            if snap_target:
                break
    
    # Check circle centers
    if not snap_target:
        for circle in circles:
            if distance(pos, circle[0]) < snap_distance:
                snap_target = circle[0]
                break
    
    # Snap to grid if no other target found
    if not snap_target and False:  # Disable grid snapping for now
        grid_x = round(pos[0] / grid_size) * grid_size
        grid_y = round(pos[1] / grid_size) * grid_size
        snap_target = (grid_x, grid_y)
    
    return snap_target if snap_target else pos

def draw_grid():
    """Draw background grid with lighter color and thinner lines"""
    for x in range(0, WIDTH, grid_size):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, grid_size):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)

def draw_buttons():
    """Draw tool selection buttons"""
    # Straightedge button
    color = LIGHT_BLUE if current_tool == TOOL_STRAIGHTEDGE else WHITE
    pygame.draw.rect(screen, color, straightedge_button)
    pygame.draw.rect(screen, BLACK, straightedge_button, 2)
    
    # Compass button
    color = LIGHT_BLUE if current_tool == TOOL_COMPASS else WHITE
    pygame.draw.rect(screen, color, compass_button)
    pygame.draw.rect(screen, BLACK, compass_button, 2)
    
    # Button labels
    straightedge_text = button_font.render("Straightedge", True, BLACK)
    compass_text = button_font.render("Compass", True, BLACK)
    
    screen.blit(straightedge_text, (straightedge_button.x + 10, straightedge_button.y + 10))
    screen.blit(compass_text, (compass_button.x + 30, compass_button.y + 10))

def draw_elements():
    """Draw all geometric elements with anti-aliasing"""
    # Draw permanent lines with anti-aliasing
    for line in lines:
        pygame.draw.aaline(screen, BLACK, line[0], line[1], True)
    
    # Draw permanent circles with anti-aliasing
    for circle in circles:
        pygame.draw.circle(screen, BLACK, (int(circle[0][0]), int(circle[0][1])), int(circle[1]), 2)
        # For anti-aliased circles, draw two circles (thickness 1 + 1 = 2)
        pygame.draw.circle(screen, BLACK, (int(circle[0][0]), int(circle[0][1])), int(circle[1])-1, 1)
    
    # Draw intersection points
    for p in intersections:
        pygame.draw.rect(screen, RED, (p[0] - 4, p[1] - 4, 8, 8))
    
    # Draw temporary line (preview) with anti-aliasing
    if temp_line and len(temp_line) == 2:
        pygame.draw.aaline(screen, BLUE, temp_line[0], temp_line[1], True)
    
    # Draw temporary circle (preview) with anti-aliasing
    if temp_circle and len(temp_circle) == 2:
        center, radius = temp_circle
        pygame.draw.circle(screen, BLUE, (int(center[0]), int(center[1])), int(radius), 2)
        pygame.draw.circle(screen, BLUE, (int(center[0]), int(center[1])), int(radius)-1, 1)

# Main loop
running = True
drawing_line = False  # 追踪是否正在绘制直线
show_snap_indicator = False  # 是否显示捕捉指示器
snap_position = None  # 捕捉到的位置

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # 处理点捕捉和视觉反馈
    snapped_pos = snap_to_point(mouse_pos)
    show_snap_indicator = snapped_pos != mouse_pos
    snap_position = snapped_pos if show_snap_indicator else None
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking a tool button
                if straightedge_button.collidepoint(event.pos):
                    current_tool = TOOL_STRAIGHTEDGE
                    temp_line = None
                    drawing_line = False
                elif compass_button.collidepoint(event.pos):
                    current_tool = TOOL_COMPASS
                    temp_circle = None
                else:
                    # 使用捕捉到的位置
                    pos_to_use = snap_position if show_snap_indicator else mouse_pos
                    
                    if current_tool == TOOL_STRAIGHTEDGE:
                        if not drawing_line:
                            # 开始绘制新直线
                            temp_line = [pos_to_use, pos_to_use]  # 初始时起点和终点相同
                            drawing_line = True
                        else:
                            # 完成直线绘制
                            temp_line[1] = pos_to_use  # 更新终点
                            lines.append((temp_line[0], temp_line[1]))
                            temp_line = None
                            drawing_line = False
                            find_all_intersections()
                    
                    elif current_tool == TOOL_COMPASS:
                        if temp_circle is None:
                            temp_circle = [pos_to_use, 0]
                        else:
                            radius = distance(temp_circle[0], pos_to_use)
                            circles.append((temp_circle[0], radius))
                            temp_circle = None
                            find_all_intersections()
        
        elif event.type == pygame.MOUSEMOTION:
            if current_tool == TOOL_COMPASS and temp_circle and len(temp_circle) == 2:
                # 使用捕捉到的位置
                pos_to_use = snap_position if show_snap_indicator else mouse_pos
                temp_circle[1] = distance(temp_circle[0], pos_to_use)
            
            elif current_tool == TOOL_STRAIGHTEDGE and drawing_line:
                # 拖动鼠标时更新直线终点，使用捕捉到的位置
                pos_to_use = snap_position if show_snap_indicator else mouse_pos
                temp_line[1] = pos_to_use
    
    # Drawing
    screen.fill(WHITE)
    draw_grid()
    
    # 显示捕捉指示器
    if show_snap_indicator:
        pygame.draw.circle(screen, GREEN, snap_position, 6, 1)
        pygame.draw.circle(screen, GREEN, snap_position, 8, 1)
    
    draw_elements()
    draw_buttons()
    
    # Display current tool status
    status_font = pygame.font.SysFont('Arial', 24)
    if current_tool == TOOL_STRAIGHTEDGE:
        if drawing_line:
            status_text = status_font.render("Drag to draw line, click to finalize", True, BLACK)
        else:
            status_text = status_font.render("Click to start drawing line", True, BLACK)
    else:
        if temp_circle and len(temp_circle) == 2:
            status_text = status_font.render("Drag to set radius, click to finalize", True, BLACK)
        else:
            status_text = status_font.render("Click to set center", True, BLACK)
    
    screen.blit(status_text, (20, HEIGHT - 40))
    
    pygame.display.flip()

pygame.quit()
sys.exit()    