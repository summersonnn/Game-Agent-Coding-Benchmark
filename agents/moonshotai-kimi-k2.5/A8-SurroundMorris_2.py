"""
Agent Code: A8-SurroundMorris
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-09 19:15:26
"""

from typing import List, Tuple

import random
from typing import List, Tuple

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
    
    def _count_adjacent(self, board: List[str], spot: int) -> Tuple[int, int, int]:
        """Return (empty_count, friendly_count, opponent_count) for spot."""
        piece = board[spot]
        empty = friendly = opp = 0
        for n in ADJACENCY[spot]:
            if board[n] == '':
                empty += 1
            elif board[n] == piece:
                friendly += 1
            else:
                opp += 1
        return empty, friendly, opp
    
    def _is_overwhelmed(self, board: List[str], spot: int) -> bool:
        """Check if piece at spot is overwhelmed (0 empty and opp > friendly)."""
        if board[spot] == '':
            return False
        empty, friendly, opp = self._count_adjacent(board, spot)
        return empty == 0 and opp > friendly
    
    def _apply_captures(self, board: List[str], active_spot: int, active_color: str) -> List[str]:
        """Apply capture rules: suicide check first, then friendly sweep, then enemy sweep."""
        new_board = list(board)
        
        # Step 1: Active piece suicide check
        if self._is_overwhelmed(new_board, active_spot):
            new_board[active_spot] = ''
            return new_board
        
        # Step 2a: Remove overwhelmed friendly pieces (self-harm priority)
        changed = True
        while changed:
            changed = False
            for s in range(24):
                if new_board[s] == active_color and self._is_overwhelmed(new_board, s):
                    new_board[s] = ''
                    changed = True
        
        # Step 2b: Remove overwhelmed enemy pieces
        opp_color = 'W' if active_color == 'B' else 'B'
        changed = True
        while changed:
            changed = False
            for s in range(24):
                if new_board[s] == opp_color and self._is_overwhelmed(new_board, s):
                    new_board[s] = ''
                    changed = True
        
        return new_board
    
    def _simulate_placement(self, board: List[str], spot: int, color: str) -> List[str]:
        """Simulate placing a piece at spot and resolve captures."""
        new_board = list(board)
        new_board[spot] = color
        return self._apply_captures(new_board, spot, color)
    
    def _simulate_movement(self, board: List[str], from_spot: int, to_spot: int, color: str) -> List[str]:
        """Simulate moving piece from from_spot to to_spot and resolve captures."""
        new_board = list(board)
        new_board[from_spot] = ''
        new_board[to_spot] = color
        return self._apply_captures(new_board, to_spot, color)
    
    def _evaluate(self, board: List[str], color: str) -> float:
        """Evaluate board from color's perspective."""
        opp = 'W' if color == 'B' else 'B'
        my_count = sum(1 for p in board if p == color)
        opp_count = sum(1 for p in board if p == opp)
        
        if my_count == 0:
            return -1000.0
        if opp_count == 0:
            return 1000.0
        
        score = (my_count - opp_count) * 10.0
        
        for spot in range(24):
            piece = board[spot]
            if piece == '':
                continue
            
            empty, friendly, opp_adj = self._count_adjacent(board, spot)
            degree = len(ADJACENCY[spot])
            
            if piece == color:
                # Penalize trapped pieces
                if empty == 0:
                    score -= 4.0
                    if opp_adj > friendly:
                        score -= 8.0
                else:
                    score += empty * 0.4
                
                # Prefer crossroads, avoid corners
                if degree == 4:
                    score += 1.0
                elif degree == 2:
                    score -= 0.3
            else:
                # Good to trap opponent
                if empty == 0:
                    score += 3.0
                    if opp_adj > friendly:
                        score += 6.0
                if degree == 4:
                    score -= 0.4
        
        return score
    
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        opp = state["opponent_color"]
        
        if phase == "placement":
            return self._placement_move(board, color, opp)
        else:
            return self._movement_move(board, color, opp, state)
    
    def _placement_move(self, board: List[str], color: str, opp: str) -> int:
        empty = [i for i in range(24) if board[i] == '']
        if not empty:
            return 0
        
        # Categorize by net material gain
        good_moves = []   # Net +1 (piece survives, no friendly fire)
        ok_moves = []     # Net 0 (suicide or trade)
        bad_moves = []    # Net negative
        
        for spot in empty:
            new_board = self._simulate_placement(board, spot, color)
            my_old = sum(1 for p in board if p == color)
            my_new = sum(1 for p in new_board if p == color)
            diff = my_new - my_old
            
            if diff == 1:
                good_moves.append(spot)
            elif diff == 0:
                ok_moves.append(spot)
            else:
                bad_moves.append(spot)
        
        candidates = good_moves if good_moves else (ok_moves if ok_moves else bad_moves)
        
        best_score = -float('inf')
        best_spots = []
        
        for spot in candidates:
            new_board = self._simulate_placement(board, spot, color)
            score = self._evaluate(new_board, color)
            
            # Positional preference
            deg = len(ADJACENCY[spot])
            if deg == 4:
                score += 2.0
            elif deg == 3:
                score += 0.5
            
            if score > best_score:
                best_score = score
                best_spots = [spot]
            elif abs(score - best_score) < 0.01:
                best_spots.append(spot)
        
        return random.choice(best_spots)
    
    def _movement_move(self, board: List[str], color: str, opp: str, state: dict) -> Tuple[int, int]:
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for n in ADJACENCY[spot]:
                if board[n] == '':
                    moves.append((spot, n))
        
        if not moves:
            return (0, 0)
        if len(moves) == 1:
            return moves[0]
        
        best_score = -float('inf')
        best_moves = []
        history = state.get("history", [])
        
        for move in moves:
            f, t = move
            new_board = self._simulate_movement(board, f, t, color)
            
            # Repetition avoidance
            future = (tuple(new_board), opp)
            if sum(1 for h in history if h == future) >= 2:
                continue  # Avoid third repetition
            
            score = self._evaluate(new_board, color)
            
            # Capture bonus
            opp_old = sum(1 for p in board if p == opp)
            opp_new = sum(1 for p in new_board if p == opp)
            if opp_new < opp_old:
                score += 15.0 * (opp_old - opp_new)
            
            # Self-loss penalty
            my_old = sum(1 for p in board if p == color)
            my_new = sum(1 for p in new_board if p == color)
            if my_new < my_old:
                score -= 20.0 * (my_old - my_new)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif abs(score - best_score) < 0.01:
                best_moves.append(move)
        
        if not best_moves:
            # All moves lead to repetition or are invalid, pick randomly
            return random.choice(moves)
        
        return random.choice(best_moves)
