import pygame
import sys
import os
import webbrowser
import subprocess
import random
import sqlite3
from typing import List, Dict, Tuple

# 初始化Pygame
pygame.init()
pygame.font.init()

# 确保中文显示正常
try:
    font_large = pygame.font.Font("simhei.ttf", 24)
    font_medium = pygame.font.Font("simhei.ttf", 16)
    font_small = pygame.font.Font("simhei.ttf", 12)
except:
    font_large = pygame.font.SysFont(["SimHei", "Microsoft YaHei", "Arial"], 24)
    font_medium = pygame.font.SysFont(["SimHei", "Microsoft YaHei", "Arial"], 16)
    font_small = pygame.font.SysFont(["SimHei", "Microsoft YaHei", "Arial"], 12)

# 游戏常量
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
CARD_WIDTH = 220
CARD_HEIGHT = 300
DECK_POS = (50, SCREEN_HEIGHT // 2 - 100)  # 左侧牌堆位置
DISCARD_PILE_POS = (SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2 - 100)  # 右侧牌堆位置
TABLE_AREA_MARGIN = 250  # 桌面区域左右边距

# 颜色定义
COLORS = {
    "bg": (30, 100, 50),  # 背景色（桌面绿）
    "card_bg": (240, 240, 230),  # 卡牌背景
    "border": (139, 69, 19),  # 卡牌边框（棕色）
    "border_hover": (218, 165, 32),  # 悬停边框（金色）
    "title": (0, 0, 0),  # 标题颜色
    "content": (50, 50, 50),  # 内容颜色
    "deck": (101, 67, 33),  # 牌堆颜色
    "discard_pile": (101, 33, 67),  # 弃牌堆颜色（深红色调）
    "text_highlight": (128, 0, 0),  # 高亮文本
    "info": (255, 255, 255)  # 信息文本颜色
}

class CardDatabaseConnection:
    """数据库连接管理器"""
    def __init__(self, db_path="cards.db"):
        self.db_path = db_path
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

class Card:
    def __init__(self, card_id: int, title: str):
        self.id = card_id
        self.title = title
        self._details = None  # 延迟加载的详细信息
        self.pos = (0, 0)
        self.hover = False
        self.selected = False
        self.visible = True
        self.animation_pos = None  # 用于移动动画
    
    @property
    def details(self) -> Dict[str, any]:
        """延迟加载卡牌详细信息"""
        if self._details is None:
            with CardDatabaseConnection() as cursor:
                cursor.execute("SELECT * FROM cards WHERE id = ?", (self.id,))
                self._details = dict(cursor.fetchone())
        return self._details
    
    @property
    def summary(self) -> str:
        return self.details["summary"]
    
    @property
    def action_type(self) -> str:
        return self.details["action_type"]
    
    @property
    def target(self) -> str:
        return self.details["target"]

    def draw(self, surface):
        # 处理动画位置
        if self.animation_pos:
            pos = self.animation_pos
            # 动画移动
            self.animation_pos = (
                pos[0] + (self.pos[0] - pos[0]) * 0.2,
                pos[1] + (self.pos[1] - pos[1]) * 0.2
            )
            # 接近目标位置时结束动画
            if abs(self.animation_pos[0] - self.pos[0]) < 2 and abs(self.animation_pos[1] - self.pos[1]) < 2:
                self.animation_pos = None
        else:
            pos = self.pos
        
        # 卡牌基础矩形
        rect = pygame.Rect(pos[0], pos[1], CARD_WIDTH, CARD_HEIGHT)
        
        # 绘制卡牌背景
        pygame.draw.rect(surface, COLORS["card_bg"], rect, border_radius=8)
        
        # 绘制边框（根据状态变化）
        border_color = COLORS["border_hover"] if self.hover else COLORS["border"]
        border_width = 3 if self.hover else 2
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=8)
        
        # 绘制标题（只显示一行，超出部分裁剪并加省略号）
        truncated_title = self.truncate_text(self.title, 12)  # 最多12字
        title_surf = font_large.render(truncated_title, True, COLORS["title"])
        title_rect = title_surf.get_rect(center=(pos[0] + CARD_WIDTH//2, pos[1] + 30))
        surface.blit(title_surf, title_rect)
        
        # 绘制分隔线
        pygame.draw.line(
            surface, COLORS["border"],
            (pos[0] + 20, pos[1] + 60),
            (pos[0] + CARD_WIDTH - 20, pos[1] + 60),
            2
        )
        
        # 绘制摘要（最多4行，超出部分裁剪）
        summary_y = pos[1] + 75
        summary_lines = self.wrap_text(self.summary, 25)  # 每行最多25字
        for line in summary_lines[:4]:  # 只显示前4行
            line_surf = font_small.render(line, True, COLORS["content"])
            surface.blit(line_surf, (pos[0] + 20, summary_y))
            summary_y += 20
        
        # 选中状态标记（金色外边框）
        if self.selected:
            pygame.draw.rect(
                surface, COLORS["border_hover"],
                (pos[0]-5, pos[1]-5, CARD_WIDTH+10, CARD_HEIGHT+10),
                2, border_radius=10
            )

    def truncate_text(self, text, max_chars):
        """截断文本并添加省略号"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def wrap_text(self, text, max_chars):
        """文本换行处理（用于摘要）"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) <= max_chars:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        return lines

    def is_clicked(self, pos):
        """检查鼠标是否点击在卡牌上"""
        rect = pygame.Rect(self.pos[0], self.pos[1], CARD_WIDTH, CARD_HEIGHT)
        return rect.collidepoint(pos)

    def activate(self):
        """执行卡牌对应的功能"""
        try:
            if self.action_type == "file":
                if os.path.exists(self.target):
                    os.startfile(self.target)
                else:
                    print(f"文件不存在: {self.target}")
            
            elif self.action_type == "dir":
                if os.path.isdir(self.target):
                    os.startfile(self.target)
                else:
                    print(f"目录不存在: {self.target}")
            
            elif self.action_type == "url":
                webbrowser.open(self.target)
            
            elif self.action_type == "app":
                if "control" in self.target:  # 系统控制面板命令
                    subprocess.Popen(self.target, shell=True)
                elif os.path.exists(self.target) or "." not in self.target:
                    subprocess.Popen(self.target, shell=True)
                else:
                    print(f"应用不存在: {self.target}")
            
            elif self.action_type == "script":
                subprocess.Popen(["python", self.target])
                
            elif self.action_type == "python_script":
                if os.path.exists(self.target):
                    subprocess.Popen(
                        ["python", self.target],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    print(f"Python脚本不存在: {self.target}")
                
        except Exception as e:
            print(f"执行失败: {str(e)}")

class Deck:
    """牌堆基类"""
    def __init__(self, pos, color, label):
        self.pos = pos
        self.color = color
        self.label = label
        self.cards = []  # 牌堆中的卡牌
        self.hover = False
        self.flash = False  # 操作时的闪烁效果
        self.flash_timer = 0
    
    @property
    def remaining(self):
        return len(self.cards)

    def draw(self, surface):
        # 绘制牌堆基础
        deck_rect = pygame.Rect(self.pos[0], self.pos[1], 150, 200)
        
        # 牌堆主体（添加纹理效果）
        pygame.draw.rect(surface, self.color, deck_rect, border_radius=8)
        
        # 绘制牌堆叠层效果
        for i in range(5):
            offset = i * 3
            layer_rect = pygame.Rect(
                self.pos[0] + offset, self.pos[1] + offset, 
                150 - offset*2, 200 - offset*2
            )
            r, g, b = self.color
            layer_color = (min(r + i*10, 200), min(g + i*5, 150), min(b + i*5, 100))
            pygame.draw.rect(surface, layer_color, layer_rect, border_radius=8)
        
        # 绘制边框（根据状态变化）
        border_color = COLORS["border_hover"] if self.hover or self.flash else COLORS["border"]
        pygame.draw.rect(surface, border_color, deck_rect, 3, border_radius=8)
        
        # 绘制剩余卡牌数
        count_surf = font_large.render(f"剩余: {self.remaining}", True, (255, 255, 255))
        count_rect = count_surf.get_rect(center=(self.pos[0] + 75, self.pos[1] + 80))
        surface.blit(count_surf, count_rect)
        
        # 绘制提示文字
        hint_surf = font_medium.render(self.label, True, (255, 255, 255))
        hint_rect = hint_surf.get_rect(center=(self.pos[0] + 75, self.pos[1] + 140))
        surface.blit(hint_surf, hint_rect)
        
        # 更新闪烁效果
        if self.flash:
            self.flash_timer += 1
            if self.flash_timer > 10:
                self.flash = False
                self.flash_timer = 0

    def is_clicked(self, pos):
        deck_rect = pygame.Rect(self.pos[0], self.pos[1], 150, 200)
        return deck_rect.collidepoint(pos)

class DrawDeck(Deck):
    """抽卡牌堆"""
    def __init__(self):
        super().__init__(DECK_POS, COLORS["deck"], "功能卡")
        self._load_all_cards()
    
    def _load_all_cards(self):
        """从数据库加载所有卡牌的ID和标题"""
        with CardDatabaseConnection() as cursor:
            cursor.execute("SELECT id, title FROM cards")
            self.cards = [(row["id"], row["title"]) for row in cursor.fetchall()]
    
    def draw_card(self):
        """从牌堆中抽取一张卡牌"""
        if self.remaining == 0:
            return None
        index = random.randint(0, self.remaining - 1)
        card_id, title = self.cards.pop(index)
        self.flash = True  # 抽卡时闪烁提示
        return Card(card_id, title)

class DiscardPile(Deck):
    """弃牌堆（自动收起的卡牌）"""
    def __init__(self):
        super().__init__(DISCARD_PILE_POS, COLORS["discard_pile"], "已收卡牌")
    
    def add_card(self, card):
        """添加卡牌到弃牌堆"""
        # 记录当前位置作为动画起点
        card.animation_pos = (card.pos[0], card.pos[1])
        # 设置目标位置为弃牌堆位置
        card.pos = (self.pos[0] + 75 - CARD_WIDTH//2, self.pos[1] + 100 - CARD_HEIGHT//2)
        self.cards.append(card)
        self.flash = True  # 添加入堆时闪烁提示
    
    def take_card(self):
        """从弃牌堆取出最后一张卡牌"""
        if self.remaining == 0:
            return None
        self.flash = True
        return self.cards.pop()

class CardGame:
    def __init__(self):
        # 创建全屏窗口
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("卡牌桌面")
        self.clock = pygame.time.Clock()
        self.running = True
        self.draw_deck = DrawDeck()
        self.discard_pile = DiscardPile()
        self.table_cards = []  # 桌面上的卡牌
        self.dragging_card = None
        self.drag_offset = (0, 0)
        self.last_click_time = 0
        self.double_click_threshold = 500  # 双击时间阈值(ms)
        self.show_help = False  # 默认不显示帮助信息
        self.max_visible_cards = self.calculate_max_visible_cards()  # 计算最大可见卡牌数
        self.target_swap_index = None  # 用于记录拖拽交换位置的目标索引

    def calculate_max_visible_cards(self):
        """计算屏幕上能显示的最大卡牌数量"""
        # 桌面可用宽度（减去两边边距，避免遮挡牌堆）
        available_width = SCREEN_WIDTH - 2 * TABLE_AREA_MARGIN
        max_cols = available_width // (CARD_WIDTH + 30)  # 计算最大列数
        max_cols = max(2, min(5, max_cols))  # 限制在2-5列之间
        
        # 计算最大行数
        max_rows = (SCREEN_HEIGHT - 200) // (CARD_HEIGHT + 30)  # 预留顶部和底部空间
        max_rows = max(2, min(4, max_rows))  # 限制在2-4行之间
        
        return max_cols * max_rows  # 最大可见卡牌数量

    def _arrange_table_cards(self):
        """智能排列桌面上的卡牌，避免遮挡牌堆"""
        # 检查是否需要自动收起卡牌
        while len(self.table_cards) > self.max_visible_cards:
            # 收起最早的卡牌
            oldest_card = self.table_cards.pop(0)
            self.discard_pile.add_card(oldest_card)
        
        # 计算桌面可用宽度（两边留出空间给牌堆）
        available_width = SCREEN_WIDTH - 2 * TABLE_AREA_MARGIN
        max_cols = available_width // (CARD_WIDTH + 30)
        max_cols = max(2, min(5, max_cols))
        
        # 计算起始X坐标（居中排列）
        total_width = max_cols * (CARD_WIDTH + 30) - 30  # 减去最后一个间距
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = 100  # 顶部留出空间
        spacing = 30
        
        # 记录每个位置的目标坐标
        target_positions = []
        for i in range(len(self.table_cards)):
            row = i // max_cols
            col = i % max_cols
            x = start_x + col * (CARD_WIDTH + spacing)
            y = start_y + row * (CARD_HEIGHT + spacing)
            target_positions.append((x, y))
        
        # 应用目标坐标，跳过正在拖拽的卡牌
        for i, card in enumerate(self.table_cards):
            if card == self.dragging_card:
                continue  # 拖拽中的卡牌不自动排列
            
            target_x, target_y = target_positions[i]
            
            # 确保卡牌在屏幕范围内
            if target_y + CARD_HEIGHT > SCREEN_HEIGHT - 50:
                continue  # 超出屏幕范围则不调整
            
            # 如果卡牌没有动画且位置不同，设置动画
            if not card.animation_pos and (abs(card.pos[0] - target_x) > 5 or abs(card.pos[1] - target_y) > 5):
                card.animation_pos = (card.pos[0], card.pos[1])
            
            # 设置目标位置
            card.pos = (target_x, target_y)

    def handle_events(self):
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False  # ESC键退出
            
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(mouse_pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self._handle_left_click(mouse_pos, current_time)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging_card:  # 结束拖动，处理交换位置
                        self._handle_drop(mouse_pos)
                        self.dragging_card = None
                        self.target_swap_index = None

    def _handle_mouse_motion(self, pos):
        # 处理鼠标悬停效果
        self.draw_deck.hover = self.draw_deck.is_clicked(pos)
        self.discard_pile.hover = self.discard_pile.is_clicked(pos)
        
        for card in self.table_cards:
            card.hover = card.is_clicked(pos)
        
        # 处理拖动
        if self.dragging_card:
            self.dragging_card.animation_pos = None  # 拖动时取消动画
            self.dragging_card.pos = (
                pos[0] - self.drag_offset[0],
                pos[1] - self.drag_offset[1]
            )
            # 限制拖动范围在桌面区域内（不覆盖牌堆）
            self.dragging_card.pos = (
                max(TABLE_AREA_MARGIN - 50, min(self.dragging_card.pos[0], SCREEN_WIDTH - TABLE_AREA_MARGIN - CARD_WIDTH + 50)),
                max(50, min(self.dragging_card.pos[1], SCREEN_HEIGHT - 100 - CARD_HEIGHT))
            )
            
            # 检测与其他卡牌的交换位置
            self._check_swap_position(pos)

    def _check_swap_position(self, pos):
        """检测拖拽时是否需要与其他卡牌交换位置"""
        if not self.dragging_card:
            return
        
        # 获取拖拽卡牌的当前索引
        dragging_index = self.table_cards.index(self.dragging_card)
        
        # 计算当前拖拽位置对应的网格索引
        available_width = SCREEN_WIDTH - 2 * TABLE_AREA_MARGIN
        max_cols = available_width // (CARD_WIDTH + 30)
        max_cols = max(2, min(5, max_cols))
        
        start_x = (SCREEN_WIDTH - (max_cols * (CARD_WIDTH + 30) - 30)) // 2
        start_y = 100
        spacing = 30
        
        # 计算拖拽位置所在的网格单元格
        cell_x = (pos[0] - start_x) // (CARD_WIDTH + spacing)
        cell_y = (pos[1] - start_y) // (CARD_HEIGHT + spacing)
        
        # 确保单元格索引有效
        if cell_x < 0 or cell_y < 0:
            self.target_swap_index = None
            return
        
        target_index = cell_y * max_cols + cell_x
        
        # 确保目标索引在有效范围内
        if 0 <= target_index < len(self.table_cards) and target_index != dragging_index:
            self.target_swap_index = target_index
        else:
            self.target_swap_index = None

    def _handle_left_click(self, pos, current_time):
        # 点击抽卡牌堆抽卡
        if self.draw_deck.is_clicked(pos):
            new_card = self.draw_deck.draw_card()
            if new_card:
                # 新卡牌从牌堆位置飞出效果
                new_card.pos = (self.draw_deck.pos[0] + 75 - CARD_WIDTH//2, 
                                self.draw_deck.pos[1] + 100 - CARD_HEIGHT//2)
                self.table_cards.append(new_card)
            return
        
        # 点击弃牌堆取回卡牌
        if self.discard_pile.is_clicked(pos):
            card = self.discard_pile.take_card()
            if card:
                # 从弃牌堆回到桌面
                self.table_cards.append(card)
            return
        
        # 处理卡牌点击
        for card in reversed(self.table_cards):  # 逆序检查，确保顶层卡牌先响应
            if card.is_clicked(pos):
                # 检查双击
                if current_time - self.last_click_time < self.double_click_threshold:
                    card.activate()  # 双击激活功能
                    self.last_click_time = 0
                    return
                
                self.last_click_time = current_time
                
                # 开始拖动
                self.dragging_card = card
                self.drag_offset = (
                    pos[0] - card.pos[0],
                    pos[1] - card.pos[1]
                )
                
                # 把点击的卡牌移到顶层（视觉上在最上方）
                self.table_cards.remove(card)
                self.table_cards.append(card)
                
                # 选中状态切换
                card.selected = not card.selected
                
                return

    def _handle_drop(self, pos):
        """处理拖拽结束，执行卡牌位置交换"""
        if not self.dragging_card or self.target_swap_index is None:
            return
        
        # 获取拖拽卡牌的当前索引
        dragging_index = self.table_cards.index(self.dragging_card)
        
        # 执行交换
        if 0 <= self.target_swap_index < len(self.table_cards):
            # 交换列表中的位置
            self.table_cards[dragging_index], self.table_cards[self.target_swap_index] = (
                self.table_cards[self.target_swap_index], self.table_cards[dragging_index]
            )
            
            # 重新排列卡牌，触发动画效果
            self._arrange_table_cards()

    def draw(self):
        self.screen.fill(COLORS["bg"])
        
        # 绘制顶部信息栏
        info_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 50)
        pygame.draw.rect(self.screen, (40, 120, 70), info_bar)
        
        # 绘制标题
        title_surf = font_large.render("卡牌桌面", True, (255, 255, 255))
        self.screen.blit(title_surf, (30, 10))
        
        # 绘制状态栏
        status_surf = font_medium.render(
            f"ESC: 退出 | 牌堆: {self.draw_deck.remaining} | 已收: {self.discard_pile.remaining}", 
            True, (255, 255, 255)
        )
        self.screen.blit(status_surf, (SCREEN_WIDTH - status_surf.get_width() - 30, 15))
        
        # 绘制牌堆
        self.draw_deck.draw(self.screen)
        self.discard_pile.draw(self.screen)
        
        # 绘制桌面上的卡牌
        for card in self.table_cards:
            card.draw(self.screen)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self._arrange_table_cards()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    # 检查数据库是否存在
    if not os.path.exists("cards.db"):
        print("错误: 未找到cards.db数据库文件")
        print("请先运行card_database.py初始化数据库")
        sys.exit(1)
    
    game = CardGame()
    game.run()
    pygame.quit()
    sys.exit()