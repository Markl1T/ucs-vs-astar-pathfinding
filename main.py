import pygame
import random
import sys

from algorithms import ucs_search, astar_search
from heuristic import pirate_heuristic

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SIDEBAR_WIDTH = 320
GRID_SIZE = 40
MAP_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH
COLS = MAP_WIDTH // GRID_SIZE
ROWS = SCREEN_HEIGHT // GRID_SIZE

# Color Palette
C_LAKE = (25, 55, 80)
C_SAND = (245, 225, 180)
C_JUNGLE = (40, 120, 40)
C_LAVA = (120, 30, 30)
C_PATH = (255, 50, 50)
C_FRONTIER = (0, 180, 255)
C_EXPLORED = (80, 80, 80, 100)
C_SHIP = (139, 69, 19)
C_KEY = (255, 215, 0)
C_CHEST = (148, 0, 211)

# Terrain Movement Costs
COST_SAND = 1
COST_JUNGLE = 5
COST_LAKE = 10


class PirateProblem:
    def __init__(self, grid, start, key_pos, chest_pos, goal):
        self.grid = grid
        self.start = start
        self.key_pos = key_pos
        self.chest_pos = chest_pos
        self.goal = goal
        self.width = len(grid[0])
        self.height = len(grid)
    
    def get_start_state(self):
        return (self.start[0], self.start[1], False, False)
    
    def is_goal(self, state):
        x, y, has_key, has_treasure = state
        return has_treasure and (x, y) == self.goal
    
    def get_successors(self, state):
        x, y, has_key, has_treasure = state
        successors = []
        
        # 4-directional movement
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            
            # Boundary check
            if not (0 <= nx < self.width and 0 <= ny < self.height):
                continue
            
            terrain = self.grid[ny][nx]
            
            # Lava is impassable
            if terrain == 'LAVA':
                continue
            
            # Determine movement cost by terrain
            if terrain == 'SAND':
                move_cost = COST_SAND
            elif terrain == 'JUNGLE':
                move_cost = COST_JUNGLE
            elif terrain == 'LAKE':
                move_cost = COST_LAKE
            else:
                move_cost = COST_SAND
            
            # Update inventory flags
            new_key = has_key or ((nx, ny) == self.key_pos)
            new_treasure = has_treasure or ((nx, ny) == self.chest_pos and new_key)
            
            next_state = (nx, ny, new_key, new_treasure)
            successors.append((next_state, move_cost))
        
        return successors
    
    def heuristic(self, state):
        return pirate_heuristic(state, self.key_pos, self.chest_pos, self.goal)


def generate_map():
    # Procedurally generate terrain grid with:
    # - Lava (impassable) ~12%
    # - Jungle (cost 5) ~25%
    # - Lake (cost 10) ~8%
    # - Sand (cost 1) default
    grid = [['SAND' for _ in range(COLS)] for _ in range(ROWS)]
    
    # Terrain generation
    for r in range(ROWS):
        for c in range(COLS):
            noise = random.random()
            if noise < 0.12:
                grid[r][c] = 'LAVA'
            elif noise < 0.37:
                grid[r][c] = 'JUNGLE'
            elif noise < 0.45:
                grid[r][c] = 'LAKE'
    
    # Place start and goal at opposite corners
    start = (2, 2)  # Top-left
    goal = (COLS - 3, ROWS - 3)  # Bottom-right
    
    # Place key and chest at other positions
    key = (COLS - 3, 2)  # Top-right
    chest = (2, ROWS - 3)  # Bottom-left
    
    # Clear critical areas to ensure solvability
    for pos in [start, goal, key, chest]:
        grid[pos[1]][pos[0]] = 'SAND'
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                grid[ny][nx] = 'SAND'
    
    return grid, start, key, chest, goal


def draw_map(screen, grid, start, goal, key, chest, search_data, path, animate_step):
    
    # Draw terrain tiles
    for r in range(ROWS):
        for c in range(COLS):
            rect = (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            # Terrain color
            terrain = grid[r][c]
            if terrain == 'LAVA':
                color = C_LAVA
            elif terrain == 'JUNGLE':
                color = C_JUNGLE
            elif terrain == 'LAKE':
                color = C_LAKE
            else:
                color = C_SAND
            
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
    
    # Draw explored nodes (semi-transparent overlay)
    if search_data and 'explored_set' in search_data:
        surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        surf.fill(C_EXPLORED)
        for state in search_data['explored_set']:
            x, y, _, _ = state
            screen.blit(surf, (x * GRID_SIZE, y * GRID_SIZE))
    
    # Highlight current frontier node
    if search_data and 'current_node' in search_data:
        node = search_data['current_node']
        x, y, _, _ = node.state
        pygame.draw.rect(screen, C_FRONTIER, 
                        (x * GRID_SIZE + 2, y * GRID_SIZE + 2, 
                         GRID_SIZE - 4, GRID_SIZE - 4), 4)
    
    # Draw final path
    if path and len(path) > 1:
        points = [(p[0] * GRID_SIZE + GRID_SIZE // 2, 
                  p[1] * GRID_SIZE + GRID_SIZE // 2) for p in path]
        if len(points) > 1:
            pygame.draw.lines(screen, C_PATH, False, points, 5)
    
    # Draw icons
    def draw_icon(pos, color, shape, label):
        cx = pos[0] * GRID_SIZE + GRID_SIZE // 2
        cy = pos[1] * GRID_SIZE + GRID_SIZE // 2
        
        if shape == 'start':
            # Green circle for START
            pygame.draw.circle(screen, (0, 200, 0), (cx, cy), 14)
            pygame.draw.circle(screen, (0, 255, 0), (cx, cy), 14, 3)
        elif shape == 'goal':
            # Red square for GOAL
            pygame.draw.rect(screen, (200, 0, 0), (cx - 14, cy - 14, 28, 28))
            pygame.draw.rect(screen, (255, 0, 0), (cx - 14, cy - 14, 28, 28), 3)
        elif shape == 'key':
            # Gold key
            pygame.draw.circle(screen, color, (cx, cy), 10)
            pygame.draw.circle(screen, (200, 170, 0), (cx, cy), 10, 3)
        elif shape == 'chest':
            # Treasure chest
            pygame.draw.rect(screen, color, (cx - 12, cy - 9, 24, 18))
            pygame.draw.rect(screen, (100, 0, 130), (cx - 12, cy - 9, 24, 18), 3)
        
        # Label
        font_small = pygame.font.SysFont("Arial", 11, bold=True)
        label_surf = font_small.render(label, True, (255, 255, 255))
        label_rect = label_surf.get_rect(center=(cx, cy + 22))
        pygame.draw.rect(screen, (0, 0, 0), label_rect.inflate(6, 2))
        screen.blit(label_surf, label_rect)
    
    draw_icon(start, C_SHIP, 'start', 'START')
    draw_icon(goal, (200, 0, 0), 'goal', 'GOAL')
    draw_icon(key, C_KEY, 'key', 'KEY')
    draw_icon(chest, C_CHEST, 'chest', 'CHEST')
    
    # Draw animated pirate moving along the path
    if path and animate_step > 0:
        current_index = min((animate_step - 1) // 10, len(path) - 1)
        pirate_pos = path[current_index]
        px = pirate_pos[0] * GRID_SIZE + GRID_SIZE // 2
        py = pirate_pos[1] * GRID_SIZE + GRID_SIZE // 2
        
        pygame.draw.circle(screen, (0, 0, 0), (px, py), 10)


def draw_sidebar(screen, current_algo, search_data, results_ucs, results_astar):
    panel = pygame.Rect(MAP_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (25, 25, 35), panel)
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 28, bold=True)
    font_head = pygame.font.SysFont("Arial", 20, bold=True)
    font_text = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)
    
    x = MAP_WIDTH + 20
    y = 20
    
    title = font_title.render("Pirate Treasure Hunt", True, (255, 200, 50))
    screen.blit(title, (x, y))
    y += 45
    
    # Controls section
    screen.blit(font_head.render("Controls", True, (100, 200, 255)), (x, y))
    y += 28
    
    controls = [
        ("[C] Compare Both", (200, 200, 200)),
        ("[U] UCS Only", (200, 200, 200)),
        ("[A] A* Only", (200, 200, 200)),
        ("[R] New Map", (200, 200, 200)),
        ("[SPACE] Fast", (200, 200, 200))
    ]
    
    for text, color in controls:
        screen.blit(font_text.render(text, True, color), (x + 5, y))
        y += 24
    
    y += 15
    
    # Current Status
    if current_algo != "None":
        status_color = (0, 255, 150) if current_algo == "COMPARE" else (255, 200, 50)
        screen.blit(font_text.render(f"Running: {current_algo}", True, status_color), (x, y))
        y += 30
    
    # Comparison Results
    if results_ucs or results_astar:
        y += 5
        screen.blit(font_head.render("Performance", True, (100, 200, 255)), (x, y))
        y += 30
        
        # Table header
        screen.blit(font_text.render("Algorithm", True, (200, 200, 200)), (x + 5, y))
        screen.blit(font_text.render("Nodes", True, (200, 200, 200)), (x + 130, y))
        y += 25
        
        # UCS row
        if results_ucs:
            screen.blit(font_text.render("UCS", True, (255, 180, 100)), (x + 5, y))
            screen.blit(font_text.render(str(results_ucs['expanded']), True, (255, 255, 255)), (x + 130, y))
            y += 24
        
        # A* row
        if results_astar:
            screen.blit(font_text.render("A*", True, (100, 255, 150)), (x + 5, y))
            screen.blit(font_text.render(str(results_astar['expanded']), True, (255, 255, 255)), (x + 130, y))
            y += 28
        
        # Show improvement
        if results_ucs and results_astar:
            improvement = ((results_ucs['expanded'] - results_astar['expanded']) / results_ucs['expanded']) * 100
            y += 5
            screen.blit(font_text.render(f"A* Efficiency: {improvement:.1f}%", True, (0, 255, 100)), (x + 5, y))
            screen.blit(font_text.render("fewer nodes!", True, (0, 255, 100)), (x + 5, y + 20))
            y += 45
        
        # Path cost (should be same for both)
        if results_ucs:
            y += 5
            screen.blit(font_text.render(f"Path Cost: {results_ucs['cost']}", True, (255, 200, 50)), (x + 5, y))
            y += 22
            screen.blit(font_small.render("(Both algorithms find", True, (150, 150, 150)), (x + 5, y))
            y += 18
            screen.blit(font_small.render("optimal solution)", True, (150, 150, 150)), (x + 5, y))



def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pirate Treasure Hunt")
    clock = pygame.time.Clock()
    
    # Initialize map and problem
    grid, start, key, chest, goal = generate_map()
    problem = PirateProblem(grid, start, key, chest, goal)
    
    # Search state
    search_gen = None
    search_data = None
    path = []
    current_algo = "None"
    running = False
    turbo = False
    animate_step = 0
    
    # Results storage
    results_ucs = None
    results_astar = None
    compare_mode = False
    compare_phase = 0  # 0: UCS, 1: A*
    
    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                # New map
                if event.key == pygame.K_r:
                    grid, start, key, chest, goal = generate_map()
                    problem = PirateProblem(grid, start, key, chest, goal)
                    search_gen = None
                    search_data = None
                    path = []
                    current_algo = "None"
                    running = False
                    animate_step = 0
                    results_ucs = None
                    results_astar = None
                    compare_mode = False
                
                # Toggle turbo mode
                if event.key == pygame.K_SPACE:
                    turbo = not turbo
                
                if event.key == pygame.K_u:
                    search_gen = ucs_search(problem)
                    search_data = None
                    path = []
                    current_algo = "UCS"
                    running = True
                    animate_step = 0
                    compare_mode = False
                
                if event.key == pygame.K_a:
                    search_gen = astar_search(problem)
                    search_data = None
                    path = []
                    current_algo = "A*"
                    running = True
                    animate_step = 0
                    compare_mode = False
                
                # Compare mode
                if event.key == pygame.K_c:
                    compare_mode = True
                    compare_phase = 0
                    results_ucs = None
                    results_astar = None
                    search_gen = ucs_search(problem)
                    search_data = None
                    path = []
                    current_algo = "COMPARE"
                    running = True
                    animate_step = 0
        
        # Run search algorithm
        if running and search_gen:
            try:
                # Run multiple steps in turbo mode
                steps = 5 if turbo else 1
                for _ in range(steps):
                    result = next(search_gen)
                    
                    if result['status'] == 'running':
                        search_data = result
                    elif result['status'] == 'success':
                        path = result['path']
                        running = False
                        
                        # Store results for comparison
                        if compare_mode:
                            if compare_phase == 0:
                                results_ucs = result
                                # Start A* next
                                compare_phase = 1
                                search_gen = astar_search(problem)
                                running = True
                                animate_step = 0
                            else:
                                results_astar = result
                                compare_mode = False
                        elif current_algo == "UCS":
                            results_ucs = result
                        elif current_algo == "A*":
                            results_astar = result
                        
                        break
                    else:
                        running = False
                        break
            except StopIteration:
                running = False
        
        # Animate the pirate along the path
        if path and not running and animate_step < len(path) * 10:
            animate_step += 1
        
        # Rendering
        screen.fill((0, 0, 0))
        draw_map(screen, grid, start, goal, key, chest, search_data, path, animate_step)
        exit_btn = draw_sidebar(screen, current_algo, search_data, results_ucs, results_astar)
        
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
