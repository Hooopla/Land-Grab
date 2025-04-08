import random

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