import pygame
import random
import time
import sys

def generate_game_board(rows, cols):
    """
    Return a 2D list 'game_board' with exactly 3 contiguous regions
    that fill the board (each cell belongs to exactly one region).

    This version uses more random region sizes rather than splitting
    rows*cols evenly among the three regions.
    """

    total_cells = rows * cols

    # -----------------------------------------------------------------
    # Region sizes
    # -----------------------------------------------------------------
    region1_size = random.randint((total_cells // 3) - 5, (total_cells // 3) + 5)
    # region1_size <= region1_size <= total_cells // 2
    region1_size = max(region1_size, min(region1_size, total_cells // 2))

    region2_size = random.randint((total_cells // 3) - 3, (total_cells // 3) + 3)
    region2_size = max((total_cells // 5), min(region2_size, total_cells - region1_size - 1))
    
    if region2_size == region1_size:
        region2_size -= 1

    region3_size = total_cells - (region1_size + region2_size)
    
    # Check for equal sizes
    if region1_size == region2_size == region3_size:
        # choose which region to reduce randomly
        c = random.randint(0, 2)
        if c == 0:
            region1_size -= 1
            region2_size -= 2
        elif c == 1:
            region2_size -= 1
            region3_size -= 2
        else:
            region3_size -= 1
            region1_size -= 2
    # Else check pairs:
    elif region1_size == region2_size:
        if region1_size > 1 and region2_size > 1:
            c = random.randint(0, 1)
            if c == 0:
                region1_size -= 1
            else:
                region2_size -= 1
    elif region1_size == region3_size:
        if region1_size > 1 and region3_size > 1:
            c = random.randint(0, 1)
            if c == 0:
                region1_size -= 1
            else:
                region3_size -= 1
    elif region2_size == region3_size:
        if region2_size > 1 and region3_size > 1:
            c = random.randint(0, 1)
            if c == 0:
                region2_size -= 1
            else:
                region3_size -= 1

    region_sizes = [region1_size, region2_size, region3_size]
    # Shuffle the region IDs so we don't always create them in the same order
    random.shuffle(region_sizes)

    # Prepare to build a random spanning tree
    # Converts (row, col) to a single index 
    def idx_of(row, col):
        return row * cols + col

    # Converts a single index to (row, col)
    def coords_of(idx):
        return (idx // cols, idx % cols)

    total_cells = rows * cols
    neighbours = {i: [] for i in range(total_cells)}
    visited = [False] * total_cells
    stack = []
    spanning_tree_edges = []

    # Random DFS to pick edges in the spanning tree
    start_idx = random.randint(0, total_cells - 1)
    visited[start_idx] = True
    stack.append(start_idx)

    directions = [(1,0),(-1,0),(0,1),(0,-1)]

    while stack:
        current = stack[-1]
        row, col = coords_of(current)

        random.shuffle(directions)
        found_unvisited = False

        for delta_row, delta_col in directions:
            neighbour_row, neighbour_col = row + delta_row, col + delta_col
            if 0 <= neighbour_row < rows and 0 <= neighbour_col < cols:
                neighbour_idx = idx_of(neighbour_row, neighbour_col)
                if not visited[neighbour_idx]:
                    spanning_tree_edges.append((current, neighbour_idx))
                    visited[neighbour_idx] = True
                    stack.append(neighbour_idx)
                    found_unvisited = True
                    break

        if not found_unvisited:
            stack.pop()

    # Populate adjacency from spanning_tree_edges
    for (u, v) in spanning_tree_edges:
        neighbours[u].append(v)
        neighbours[v].append(u)

    region_of = [-1] * total_cells

    def size_and_nodes_of_subtree(start_idx, blocked_edge=None):
        """
        Return the set of nodes reachable from start_idx without crossing 'blocked_edge'.
        'blocked_edge' is a tuple (a,b) that we treat as 'cut' (not traversable).
        """
        stack_local = [start_idx]
        subtree_nodes = set([start_idx])
        while stack_local:
            current_idx = stack_local.pop()
            for next in neighbours[current_idx]:
                if blocked_edge:
                    a, b = blocked_edge
                    if (current_idx == a and next == b) or (current_idx == b and next == a):
                        continue
                if next not in subtree_nodes and region_of[next] == -1:
                    subtree_nodes.add(next)
                    stack_local.append(next)
        return subtree_nodes

    def create_region(region_id, desired_size):
        """
        BFS-based `carving` approach where the size is drawn from the random region_sizes array.
        """
        unassigned = [i for i in range(total_cells) if region_of[i] == -1]
        if not unassigned:
            return False
        root_candidate = random.choice(unassigned)

        # Entire connected component
        entire_cc = size_and_nodes_of_subtree(root_candidate, blocked_edge=None)

        if len(entire_cc) <= desired_size:
            for n in entire_cc:
                region_of[n] = region_id
            return True

        best_subtree = None
        best_diff = None

        # We'll randomize the edges we try to "cut"
        all_edges = []
        for (u, v) in spanning_tree_edges:
            if (u in entire_cc) and (v in entire_cc):
                all_edges.append((u, v))
        random.shuffle(all_edges)

        for (u, v) in all_edges:
            sub_u = size_and_nodes_of_subtree(u, blocked_edge=(u, v))
            diff_u = abs(len(sub_u) - desired_size)

            if best_subtree is None or diff_u < best_diff:
                best_subtree = sub_u
                best_diff = diff_u
                if best_diff == 0:
                    break

            sub_v = size_and_nodes_of_subtree(v, blocked_edge=(u, v))
            diff_v = abs(len(sub_v) - desired_size)
            if diff_v < best_diff:
                best_subtree = sub_v
                best_diff = diff_v
                if best_diff == 0:
                    break

        if best_subtree:
            for n in best_subtree:
                region_of[n] = region_id
            return True
        else:
            return False

    #
    # Create out each region using the *shuffled* region_sizes
    #
    # e.g., region 0 => region_sizes[0], region 1 => region_sizes[1], region 2 => region_sizes[2]
    create_region(0, region_sizes[0])
    create_region(1, region_sizes[1])

    # anything left => region 2
    region_of = [2 if reg == -1 else reg for reg in region_of]

    # Build final 2D board
    game_board = [[-1]*cols for _ in range(rows)]
    for idx, reg_id in enumerate(region_of):
        row, col = coords_of(idx)
        game_board[row][col] = reg_id

    return game_board

# ---------------------------------------------------------------------
# Rendering functions
# ---------------------------------------------------------------------

def draw_shape_outlines(surface, game_board, rows, cols,
                        cell_width, cell_height, outline_color=(0, 0, 0)):
    """Draw outlines for each region."""
    for row in range(rows):
        for col in range(cols):
            current_shape_id = game_board[row][col]
            x = BOARD_OFFSET_X + col * cell_width
            y = BOARD_OFFSET_Y + row * cell_height
            rect = pygame.Rect(x, y, cell_width, cell_height)
            # Top boundary?
            if row == 0 or game_board[row - 1][col] != current_shape_id:
                pygame.draw.line(surface, outline_color, rect.topleft, rect.topright, 3)
            # Bottom boundary?
            if row == rows - 1 or game_board[row + 1][col] != current_shape_id:
                pygame.draw.line(surface, outline_color, rect.bottomleft, rect.bottomright, 3)
            # Left boundary?
            if col == 0 or game_board[row][col - 1] != current_shape_id:
                pygame.draw.line(surface, outline_color, rect.topleft, rect.bottomleft, 3)
            # Right boundary?
            if col == cols - 1 or game_board[row][col + 1] != current_shape_id:
                pygame.draw.line(surface, outline_color, rect.topright, rect.bottomright, 3)
                
    
def reveal_shapes(surface, game_board, rows, cols, cell_width, cell_height, shape_colors, region_revealed):
    """
    Fill only the shapes that have been revealed/claimed.
    region_revealed is a list [bool, bool, bool], indicating if region i is revealed.
    """
    for row in range(rows):
        for col in range(cols):
            shape_id = game_board[row][col]
            # compute offset coordinates
            x = BOARD_OFFSET_X + col * cell_width
            y = BOARD_OFFSET_Y + row * cell_height

            if region_revealed[shape_id]:
                color = shape_colors[shape_id % len(shape_colors)]
                rect = pygame.Rect(x, y, cell_width, cell_height)
                pygame.draw.rect(surface, color, rect)

def draw_grid_outlines(surface, rows, cols, cell_width, cell_height, offset_x, offset_y, outline_color=(0,0,0)):
    """
    Draws a simple rectangular grid with black lines between cells,
    offset by (offset_x, offset_y).
    """
    # Vertical lines
    for col in range(cols + 1):
        x = offset_x + (col * cell_width)
        start_pos = (x, offset_y)
        end_pos = (x, offset_y + rows * cell_height)
        pygame.draw.line(surface, outline_color, start_pos, end_pos, 2)

    # Horizontal lines
    for row in range(rows + 1):
        y = offset_y + (row * cell_height)
        start_pos = (offset_x, y)
        end_pos = (offset_x + cols * cell_width, y)
        pygame.draw.line(surface, outline_color, start_pos, end_pos, 2)
        
def count_region_cells(game_board):
    """
    Returns a list of length 3: [count_region0, count_region1, count_region2].
    """
    region_counts = [0, 0, 0]
    for row in game_board:
        for cell_id in row:
            region_counts[cell_id] += 1
    return region_counts

# Map from region id to color (For now)
REGION_COLOR_NAMES = {
    0: "Red",
    1: "Green",
    2: "Blue"
}

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1520, 960
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Stake Your Claim!")

# Grid dimensions
ROWS, COLS = 7, 9

# Generate the board
game_board = generate_game_board(ROWS, COLS)

# Color for each region
PLAYER_COLORS = [(255, 0, 0),   # Red
                 (0, 255, 0),   # Green
                 (0, 0, 255)]   # Blue

CELL_WIDTH = 85
CELL_HEIGHT = 85

total_board_width = CELL_WIDTH * COLS
total_board_height = CELL_HEIGHT * ROWS

BOARD_OFFSET_X = (SCREEN_WIDTH - total_board_width) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - total_board_height) // 2
SCREEN_COLOUR = (128, 128, 128)

show_outlines = True
show_full_shapes = False
show_grid_outlines = False
region_revealed = [False, False, False]

clock = pygame.time.Clock()
winner_declared = False

def main():
    global show_outlines, show_full_shapes, show_grid_outlines, winner_declared, region_revealed
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                col_clicked = (mouse_x - BOARD_OFFSET_X) // CELL_WIDTH
                row_clicked = (mouse_y - BOARD_OFFSET_Y) // CELL_HEIGHT
                
                clicked_region_id = game_board[row_clicked][col_clicked]
                
                if not region_revealed[clicked_region_id]:
                    region_revealed[clicked_region_id] = True
                    print(f"Region {REGION_COLOR_NAMES[clicked_region_id]} revealed!")
                    
                    # Check if all 3 are revealed => announce winner
                    if not winner_declared and all(region_revealed):
                        show_grid_outlines = True
                        region_counts = count_region_cells(game_board)
                        max_cells = max(region_counts)
                        winner = region_counts.index(max_cells)
                        color_name = REGION_COLOR_NAMES[winner]
                        print(f"The {color_name} region has the most cells with {max_cells}!")
                        print(f'{REGION_COLOR_NAMES[(winner + 1) % 3]} has {region_counts[(winner + 1) % 3]} cells')
                        print(f'{REGION_COLOR_NAMES[(winner + 2) % 3]} has {region_counts[(winner + 2) % 3]} cells')
                        winner_declared = True

        # Clear background
        screen.fill(SCREEN_COLOUR)

        # Draw shapes
        reveal_shapes(screen, game_board, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT, PLAYER_COLORS, region_revealed)
            
            
        if show_outlines:
            draw_shape_outlines(screen, game_board, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT)
        if show_grid_outlines:
            draw_grid_outlines(screen, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT, BOARD_OFFSET_X, BOARD_OFFSET_Y, (0,0,0))

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()
