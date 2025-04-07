# board_utils.py
import pygame

def draw_shape_outlines(surface, game_board, rows, cols,
                        cell_width, cell_height, board_offset_x, board_offset_y, outline_color=(0, 0, 0)):
    """Draw outlines for each region."""
    for row in range(rows):
        for col in range(cols):
            current_shape_id = game_board[row][col]
            x = board_offset_x + col * cell_width
            y = board_offset_y + row * cell_height
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


def reveal_shapes(surface, game_board, rows, cols, cell_width, cell_height, board_offset_x, board_offset_y, 
                  shape_colors, region_revealed, region_owner):
    """
    Fill only the shapes that have been revealed/claimed.
    If a region is revealed, use the color corresponding to the owner of that region.
    """
    for row in range(rows):
        for col in range(cols):
            shape_id = game_board[row][col]
            # compute offset coordinates
            x = board_offset_x + col * cell_width
            y = board_offset_y + row * cell_height
            rect = pygame.Rect(x, y, cell_width, cell_height)
            if region_revealed[shape_id]:
                owner = region_owner[shape_id]
                if owner is not None:
                    color = shape_colors[owner % len(shape_colors)]
                else:
                    color = shape_colors[shape_id % len(shape_colors)]
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