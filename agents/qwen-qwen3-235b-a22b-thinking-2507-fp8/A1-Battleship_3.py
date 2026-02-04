"""
Agent Code: A1-Battleship
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 3
Generated: 2026-02-04 16:22:40
"""



class BattleshipAgent:
    """
    Your agent implementation goes here.
    Implement smart bombing logic to beat your opponent.
    """
    def __init__(self, name, board_size, ships_config):
        self.name = name
        self.board_size = board_size
        self.ships_config = ships_config
        self.board_state = [['.' for _ in range(board_size)] for _ in range(board_size)]
        self.remaining_ships = list(ships_config)

    def _hunting_mode_move(self):
        prob_grid = [[0] * self.board_size for _ in range(self.board_size)]
        
        for ship_length in self.remaining_ships:
            for r in range(self.board_size):
                for c in range(0, self.board_size - ship_length + 1):
                    valid = True
                    for i in range(ship_length):
                        if self.board_state[r][c+i] != '.':
                            valid = False
                            break
                    if valid:
                        for i in range(ship_length):
                            prob_grid[r][c+i] += 1
            
            for c in range(self.board_size):
                for r in range(0, self.board_size - ship_length + 1):
                    valid = True
                    for i in range(ship_length):
                        if self.board_state[r+i][c] != '.':
                            valid = False
                            break
                    if valid:
                        for i in range(ship_length):
                            prob_grid[r+i][c] += 1
        
        max_prob = -1
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board_state[r][c] == '.':
                    if prob_grid[r][c] > max_prob:
                        max_prob = prob_grid[r][c]
                        candidates = [(r, c)]
                    elif prob_grid[r][c] == max_prob:
                        candidates.append((r, c))
        
        if not candidates:
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.board_state[r][c] == '.':
                        return (r, c)
            return (0, 0)
        
        return random.choice(candidates)

    def make_move(self, last_shot_result=None, last_shot_coord=None):
        sunk_coords = []
        
        if last_shot_result is not None:
            r_prev, c_prev = last_shot_coord
            if last_shot_result == 'MISS':
                self.board_state[r_prev][c_prev] = 'M'
            else:
                self.board_state[r_prev][c_prev] = 'H'
                r, c = r_prev, c_prev
                left = right = up = down = 0
                
                temp = c - 1
                while temp >= 0 and self.board_state[r][temp] == 'H':
                    left += 1
                    temp -= 1
                temp = c + 1
                while temp < self.board_size and self.board_state[r][temp] == 'H':
                    right += 1
                    temp += 1
                total_h = left + 1 + right
                
                temp = r - 1
                while temp >= 0 and self.board_state[temp][c] == 'H':
                    up += 1
                    temp -= 1
                temp = r + 1
                while temp < self.board_size and self.board_state[temp][c] == 'H':
                    down += 1
                    temp += 1
                total_v = up + 1 + down
                
                if total_h in self.remaining_ships:
                    coords = []
                    temp = c
                    while temp >= 0 and self.board_state[r][temp] == 'H':
                        coords.append((r, temp))
                        temp -= 1
                    temp = c + 1
                    while temp < self.board_size and self.board_state[r][temp] == 'H':
                        coords.append((r, temp))
                        temp += 1
                    sunk_coords = coords
                elif total_v in self.remaining_ships:
                    coords = []
                    temp = r
                    while temp >= 0 and self.board_state[temp][c] == 'H':
                        coords.append((temp, c))
                        temp -= 1
                    temp = r + 1
                    while temp < self.board_size and self.board_state[temp][c] == 'H':
                        coords.append((temp, c))
                        temp += 1
                    sunk_coords = coords
                
                if sunk_coords:
                    for (rr, cc) in sunk_coords:
                        self.board_state[rr][cc] = 'S'
                    ship_length = len(sunk_coords)
                    if ship_length in self.remaining_ships:
                        self.remaining_ships.remove(ship_length)
        
        active_hits_exist = any(self.board_state[i][j] == 'H' 
                               for i in range(self.board_size) 
                               for j in range(self.board_size))
        
        if active_hits_exist:
            definite_clusters = []
            visited = set()
            board = self.board_state
            
            for r in range(self.board_size):
                c = 0
                while c < self.board_size:
                    if board[r][c] == 'H' and (r, c) not in visited:
                        c2 = c
                        while c2 < self.board_size and board[r][c2] == 'H':
                            c2 += 1
                        cluster_size = c2 - c
                        if cluster_size >= 2:
                            cluster = [(r, c + i) for i in range(cluster_size)]
                            definite_clusters.append((cluster, 'horizontal'))
                            for i in range(cluster_size):
                                visited.add((r, c + i))
                        c = c2
                    else:
                        c += 1
            
            for c in range(self.board_size):
                r = 0
                while r < self.board_size:
                    if board[r][c] == 'H' and (r, c) not in visited:
                        r2 = r
                        while r2 < self.board_size and board[r2][c] == 'H':
                            r2 += 1
                        cluster_size = r2 - r
                        if cluster_size >= 2:
                            cluster = [(r + i, c) for i in range(cluster_size)]
                            definite_clusters.append((cluster, 'vertical'))
                            for i in range(cluster_size):
                                visited.add((r + i, c))
                        r = r2
                    else:
                        r += 1
            
            indefinite_clusters = []
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if board[r][c] == 'H' and (r, c) not in visited:
                        indefinite_clusters.append((r, c))
            
            definite_clusters.sort(key=lambda x: len(x[0]), reverse=True)
            
            if definite_clusters:
                cluster, direction = definite_clusters[0]
                if direction == 'horizontal':
                    r0 = cluster[0][0]
                    c_min = min(coord[1] for coord in cluster)
                    c_max = max(coord[1] for coord in cluster)
                    if c_min - 1 >= 0 and board[r0][c_min - 1] == '.':
                        move = (r0, c_min - 1)
                    elif c_max + 1 < self.board_size and board[r0][c_max + 1] == '.':
                        move = (r0, c_max + 1)
                    else:
                        move = self._hunting_mode_move()
                else:
                    c0 = cluster[0][1]
                    r_min = min(coord[0] for coord in cluster)
                    r_max = max(coord[0] for coord in cluster)
                    if r_min - 1 >= 0 and board[r_min - 1][c0] == '.':
                        move = (r_min - 1, c0)
                    elif r_max + 1 < self.board_size and board[r_max + 1][c0] == '.':
                        move = (r_max + 1, c0)
                    else:
                        move = self._hunting_mode_move()
            elif indefinite_clusters:
                r, c = indefinite_clusters[0]
                for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board[nr][nc] == '.':
                        move = (nr, nc)
                        break
                else:
                    move = self._hunting_mode_move()
            else:
                move = self._hunting_mode_move()
        else:
            move = self._hunting_mode_move()
        
        return (move, sunk_coords)
