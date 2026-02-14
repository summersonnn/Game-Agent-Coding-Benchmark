"""
Agent Code: A8-SurroundMorris
Model: qwen-qwen3-max-thinking
Run: 1
Generated: 2026-02-09 19:15:26
"""

import random
from typing import List, Tuple, Dict

class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
    
    def make_move(self, state: dict, feedback: dict | None = None):
        board = state["board"]
        phase = state["phase"]
        color = state["your_color"]
        
        if phase == "placement":
            return self._make_placement_move(board, color, state["pieces_in_hand"])
        else:
            return self._make_movement_move(board, color, state["history"])
    
    def _make_placement_move(self, board: List[str], color: str, pieces_in_hand: Dict[str, int]) -> int:
        empty_spots = [i for i in range(24) if board[i] == '']
        if not empty_spots:
            return 0
        
        best_score = float('-inf')
        best_spot = empty_spots[0]
        
        for spot in empty_spots:
            new_board = board.copy()
            new_board[spot] = color
            
            if self._is_captured(new_board, spot, color):
                my_pieces_after = sum(1 for p in new_board if p == color) - 1
                pieces_remaining = my_pieces_after + (pieces_in_hand[color] - 1)
                if pieces_remaining == 0:
                    score = -10000
                else:
                    score = -500
            else:
                new_board = self._resolve_captures(new_board, spot, color, is_placement=True)
                score = self._evaluate_board(new_board, color)
                
                if spot in [4, 10, 13, 19]:
                    score += 30
                elif spot in [7, 16]:
                    score += 20
                elif len(ADJACENCY[spot]) == 3:
                    score += 10
            
            if score > best_score:
                best_score = score
                best_spot = spot
        
        return best_spot
    
    def _make_movement_move(self, board: List[str], color: str, history: List[Tuple]) -> Tuple[int, int]:
        moves = self._get_legal_moves(board, color)
        if not moves:
            return (0, 1)
        
        opp_color = 'W' if color == 'B' else 'B'
        best_score = float('-inf')
        best_move = moves[0]
        
        for move in moves:
            new_board = self._simulate_move(board, move[0], move[1], color)
            
            if sum(1 for p in new_board if p == opp_color) == 0:
                return move
            
            my_pieces = sum(1 for p in new_board if p == color)
            if my_pieces == 0:
                continue
            
            board_tuple = tuple(new_board)
            rep_count = sum(1 for h in history if h[0] == board_tuple and h[1] == opp_color)
            if rep_count >= 2:
                my_count = sum(1 for p in board if p == color)
                opp_count = sum(1 for p in board if p == opp_color)
                if my_count >= opp_count:
                    continue
            
            score = self._evaluate_board(new_board, color)
            captured = sum(1 for i in range(24) if board[i] != '' and new_board[i] == '' and board[i] == opp_color)
            score += captured * 150
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _is_captured(self, board: List[str], spot: int, color: str) -> bool:
        if board[spot] != color:
            return False
        opp = 'W' if color == 'B' else 'B'
        empty = friendly = enemy = 0
        for nb in ADJACENCY[spot]:
            if board[nb] == '':
                empty += 1
            elif board[nb] == color:
                friendly += 1
            else:
                enemy += 1
        return empty == 0 and enemy > friendly
    
    def _resolve_captures(self, board: List[str], active_spot: int, mover_color: str, is_placement: bool = False) -> List[str]:
        new_board = board.copy()
        opp_color = 'W' if mover_color == 'B' else 'B'
        
        if self._is_captured(new_board, active_spot, mover_color):
            new_board[active_spot] = ''
            return new_board
        
        to_remove = [s for s in range(24) if new_board[s] == mover_color and self._is_captured(new_board, s, mover_color)]
        for s in to_remove:
            new_board[s] = ''
        
        to_remove = [s for s in range(24) if new_board[s] == opp_color and self._is_captured(new_board, s, opp_color)]
        for s in to_remove:
            new_board[s] = ''
        
        return new_board
    
    def _simulate_move(self, board: List[str], from_spot: int, to_spot: int, color: str) -> List[str]:
        new_board = board.copy()
        new_board[from_spot] = ''
        new_board[to_spot] = color
        return self._resolve_captures(new_board, to_spot, color)
    
    def _evaluate_board(self, board: List[str], color: str) -> int:
        opp = 'W' if color == 'B' else 'B'
        
        my_pieces = sum(1 for p in board if p == color)
        opp_pieces = sum(1 for p in board if p == opp)
        score = (my_pieces - opp_pieces) * 120
        
        if opp_pieces == 0:
            return 10000
        if my_pieces == 0:
            return -10000
        
        my_moves = self._get_legal_moves(board, color)
        opp_moves = self._get_legal_moves(board, opp)
        score += (len(my_moves) - len(opp_moves)) * 18
        
        key_crossroads = [4, 10, 13, 19]
        for spot in key_crossroads:
            if board[spot] == color:
                score += 35
            elif board[spot] == opp:
                score -= 35
        
        for spot in range(24):
            if board[spot] == color:
                empty = sum(1 for nb in ADJACENCY[spot] if board[nb] == '')
                if empty > 0:
                    score += 12
                else:
                    score -= 25
            elif board[spot] == opp:
                empty = sum(1 for nb in ADJACENCY[spot] if board[nb] == '')
                if empty == 0:
                    score += 40
        
        for spot in range(24):
            if board[spot] == opp:
                empty = sum(1 for nb in ADJACENCY[spot] if board[nb] == '')
                if empty == 1:
                    score += 28
        
        return score
    
    def _get_legal_moves(self, board: List[str], color: str) -> List[Tuple[int, int]]:
        moves = []
        for spot in range(24):
            if board[spot] != color:
                continue
            for nb in ADJACENCY[spot]:
                if board[nb] == '':
                    moves.append((spot, nb))
        return moves