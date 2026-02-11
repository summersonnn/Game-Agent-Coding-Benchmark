"""
Agent Code: A1-Battleship
Model: xiaomi/mimo-v2-flash
Run: 2
Generated: 2026-02-11 19:24:56
"""

from collections import deque

import random
from collections import deque

class BattleshipAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.target_queue = deque()
        self.target_set = set()
        self.hunt_pattern1 = []
        self.hunt_pattern2 = []
        for r in range(board_size):
            for c in range(board_size):
                if (r + c) % 2 == 0:
                    self.hunt_pattern1.append((r, c))
                else:
                    self.hunt_pattern2.append((r, c))
        self.index1 = 0
        self.index2 = 0

    def clean_target_queue(self, shot_set):
        new_queue = deque()
        new_set = set()
        while self.target_queue:
            t = self.target_queue.popleft()
            if t not in shot_set:
                new_queue.append(t)
                new_set.add(t)
        self.target_queue = new_queue
        self.target_set = new_set

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            board = state['my_board']
            ship_length = state['ships_to_place'][0]
            placements = []
            for orientation in ['horizontal', 'vertical']:
                if orientation == 'horizontal':
                    for r in range(self.board_size):
                        for c in range(self.board_size - ship_length + 1):
                            valid = True
                            for i in range(ship_length):
                                if board[r][c + i] != 'O':
                                    valid = False
                                    break
                            if valid:
                                placements.append((ship_length, (r, c), orientation))
                else:
                    for r in range(self.board_size - ship_length + 1):
                        for c in range(self.board_size):
                            valid = True
                            for i in range(ship_length):
                                if board[r + i][c] != 'O':
                                    valid = False
                                    break
                            if valid:
                                placements.append((ship_length, (r, c), orientation))
            non_adjacent_placements = []
            for placement in placements:
                L, (r, c), orientation = placement
                valid_placement = True
                if orientation == 'horizontal':
                    for i in range(L):
                        if not self.is_safe_cell(r, c + i, board):
                            valid_placement = False
                            break
                else:
                    for i in range(L):
                        if not self.is_safe_cell(r + i, c, board):
                            valid_placement = False
                            break
                if valid_placement:
                    non_adjacent_placements.append(placement)
            if non_adjacent_placements:
                chosen = random.choice(non_adjacent_placements)
            elif placements:
                chosen = random.choice(placements)
            else:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    r = random.randint(0, self.board_size - 1)
                    c = random.randint(0, self.board_size - ship_length)
                else:
                    r = random.randint(0, self.board_size - ship_length)
                    c = random.randint(0, self.board_size - 1)
                return {
                    'ship_length': ship_length,
                    'start': (r, c),
                    'orientation': orientation
                }
            return {
                'ship_length': chosen[0],
                'start': chosen[1],
                'orientation': chosen[2]
            }
        else:
            shot_set = set(shot['coord'] for shot in state['shot_history'])
            self.clean_target_queue(shot_set)
            if state['last_shot_result'] == 'HIT' and state['last_shot_coord'] is not None:
                last_shot = state['last_shot_coord']
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = last_shot[0] + dr, last_shot[1] + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if (nr, nc) not in shot_set and (nr, nc) not in self.target_set:
                            self.target_queue.append((nr, nc))
                            self.target_set.add((nr, nc))
            if self.target_queue:
                target = self.target_queue.popleft()
                self.target_set.discard(target)
                return {'target': target}
            else:
                while self.index1 < len(self.hunt_pattern1) and self.hunt_pattern1[self.index1] in shot_set:
                    self.index1 += 1
                if self.index1 < len(self.hunt_pattern1):
                    target = self.hunt_pattern1[self.index1]
                    self.index1 += 1
                    return {'target': target}
                else:
                    while self.index2 < len(self.hunt_pattern2) and self.hunt_pattern2[self.index2] in shot_set:
                        self.index2 += 1
                    if self.index2 < len(self.hunt_pattern2):
                        target = self.hunt_pattern2[self.index2]
                        self.index2 += 1
                        return {'target': target}
                    else:
                        all_cells = [(r, c) for r in range(self.board_size) for c in range(self.board_size)]
                        unvisited = [cell for cell in all_cells if cell not in shot_set]
                        if unvisited:
                            target = random.choice(unvisited)
                        else:
                            target = (0, 0)
                        return {'target': target}

    def is_safe_cell(self, r, c, board):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                if board[nr][nc] == 'S':
                    return False
        return True
