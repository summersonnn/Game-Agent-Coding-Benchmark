"""
Surround Morris Match Runner: Orchestrates head-to-head matches for A8-SurroundMorris.

Nine Men's Morris variant where capture uses spatial surrounding instead of mill
formation. 24-spot board, placement then movement phases, with the "overwhelm"
capture rule: a piece is captured when it has zero empty neighbors AND more
opponent neighbors than friendly neighbors.
"""

import argparse
import asyncio
from datetime import datetime
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add utils directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard

logger = setup_logging(__name__)

load_dotenv()

# Configuration
try:
    NUM_GAMES_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 100

try:
    MAX_TURNS_PER_GAME = int(os.getenv("MAX_TURNS_PER_GAME", "200"))
except (ValueError, TypeError):
    MAX_TURNS_PER_GAME = 200

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "surround_morris"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A8-SurroundMorris"


# ============================================================
# Shared game engine code (used by both match and human modes)
# ============================================================
GAME_ENGINE_CODE = r'''
ADJACENCY = {
    0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
    3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
    6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
    9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
    18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
}


class SurroundMorrisGame:
    """Manages the Surround Morris game state and rules."""

    def __init__(self):
        self.board = [''] * 24
        self.phase = 'placement'
        self.pieces_in_hand = {'B': 7, 'W': 7}
        self.pieces_on_board = {'B': 0, 'W': 0}
        self.current_player = 'B'
        self.move_count = 0
        self.history = []

    def opponent(self, color):
        return 'W' if color == 'B' else 'B'

    def is_captured(self, spot, board=None):
        """
        Check if the piece at spot satisfies the capture condition.
        Captured when: zero empty neighbors AND opponent neighbors > friendly neighbors.
        """
        b = board if board is not None else self.board
        piece = b[spot]
        if not piece:
            return False

        opp = self.opponent(piece)
        empty_count = 0
        friendly_count = 0
        opp_count = 0

        for neighbor in ADJACENCY[spot]:
            n = b[neighbor]
            if n == '':
                empty_count += 1
            elif n == piece:
                friendly_count += 1
            else:
                opp_count += 1

        return empty_count == 0 and opp_count > friendly_count

    def validate_placement(self, spot, color):
        if not isinstance(spot, int) or spot < 0 or spot > 23:
            return False, f"Spot {spot} out of range [0, 23]", "INVALID_SPOT_OOB"
        if self.board[spot] != '':
            return False, f"Spot {spot} is occupied by '{self.board[spot]}'", "INVALID_SPOT_OCCUPIED"
        if self.phase != 'placement':
            return False, "Not in placement phase", "INVALID_WRONG_PHASE"
        return True, "Valid", ""

    def validate_movement(self, from_spot, to_spot, color):
        if self.phase != 'movement':
            return False, "Not in movement phase", "INVALID_WRONG_PHASE"
        if not isinstance(from_spot, int) or from_spot < 0 or from_spot > 23:
            return False, f"Source {from_spot} out of range [0, 23]", "INVALID_SPOT_OOB"
        if not isinstance(to_spot, int) or to_spot < 0 or to_spot > 23:
            return False, f"Destination {to_spot} out of range [0, 23]", "INVALID_DEST_OOB"
        if self.board[from_spot] != color:
            actual = self.board[from_spot]
            return False, f"Spot {from_spot} has '{actual}', not your piece '{color}'", "INVALID_NOT_YOUR_PIECE"
        if self.board[to_spot] != '':
            return False, f"Destination {to_spot} is occupied", "INVALID_DEST_OCCUPIED"
        if to_spot not in ADJACENCY[from_spot]:
            return False, f"Spots {from_spot} and {to_spot} are not adjacent", "INVALID_NOT_ADJACENT"
        return True, "Valid", ""

    def _capture_sweep(self, color):
        """
        Universal capture sweep with self-harm priority.
        1. Remove mover's captured pieces first.
        2. Re-check enemy pieces (may have gained empty neighbors from step 1).
        """
        captured = []
        opp = self.opponent(color)

        for s in range(24):
            if self.board[s] == color and self.is_captured(s):
                self.board[s] = ''
                self.pieces_on_board[color] -= 1
                captured.append(s)

        for s in range(24):
            if self.board[s] == opp and self.is_captured(s):
                self.board[s] = ''
                self.pieces_on_board[opp] -= 1
                captured.append(s)

        return captured

    def apply_placement(self, spot, color):
        """
        Place a piece. Suicide check first, then sweep with self-harm priority.
        """
        self.board[spot] = color
        self.pieces_in_hand[color] -= 1
        self.pieces_on_board[color] += 1

        captured = []

        if self.is_captured(spot):
            self.board[spot] = ''
            self.pieces_on_board[color] -= 1
            captured.append(spot)
            return captured

        captured.extend(self._capture_sweep(color))
        return captured

    def apply_movement(self, from_spot, to_spot, color):
        """
        Move a piece. Suicide check first, then sweep with self-harm priority.
        """
        self.board[from_spot] = ''
        self.board[to_spot] = color

        captured = []

        if self.is_captured(to_spot):
            self.board[to_spot] = ''
            self.pieces_on_board[color] -= 1
            captured.append(to_spot)
            return captured

        captured.extend(self._capture_sweep(color))
        return captured

    def get_legal_placements(self, color):
        return [s for s in range(24) if self.board[s] == '']

    def get_legal_movements(self, color):
        moves = []
        for f in range(24):
            if self.board[f] != color:
                continue
            for t in ADJACENCY[f]:
                if self.board[t] == '':
                    moves.append((f, t))
        return moves

    def record_history(self):
        self.history.append((tuple(self.board), self.current_player))

    def check_repetition(self):
        """
        Check 3-fold repetition. Call after record_history(), BEFORE move.
        Returns (is_over, description) or (False, None).
        """
        current_state = (tuple(self.board), self.current_player)
        if self.history.count(current_state) >= 3:
            return True, "Draw by Repetition"
        return False, None

    def check_elimination(self):
        """
        Check if either player is eliminated. Call AFTER move.
        Self-harm priority: check mover (current_player) first.
        During placement, a player is only eliminated if they have 0 on board AND 0 in hand.
        """
        opp = self.opponent(self.current_player)

        mover_alive = self.pieces_on_board[self.current_player] > 0 or \
                      (self.phase == 'placement' and self.pieces_in_hand[self.current_player] > 0)
        opp_alive = self.pieces_on_board[opp] > 0 or \
                    (self.phase == 'placement' and self.pieces_in_hand[opp] > 0)

        if not mover_alive:
            return True, f"{opp} wins ({self.current_player} has 0 pieces)"
        if not opp_alive:
            return True, f"{self.current_player} wins ({opp} has 0 pieces)"
        return False, None

    def check_turn_limit(self):
        """Check movement turn limit. Call AFTER move and move_count increment."""
        if self.phase == 'movement' and self.move_count >= MAX_TURNS:
            return True, f"Draw ({MAX_TURNS} movement turns reached)"
        return False, None

    def check_phase_transition(self):
        if self.phase == 'placement' and self.pieces_in_hand['B'] == 0 and self.pieces_in_hand['W'] == 0:
            self.phase = 'movement'
            self.move_count = 0
            self.history = []

    def display_board(self):
        def p(i):
            v = self.board[i]
            return v if v else '.'
        print(f" {p(0)}----------{p(1)}----------{p(2)}")
        print(f" |           |           |")
        print(f" |   {p(3)}-------{p(4)}-------{p(5)}   |")
        print(f" |   |       |       |   |")
        print(f" |   |   {p(6)}---{p(7)}---{p(8)}   |   |")
        print(f" |   |   |       |   |   |")
        print(f" {p(9)}---{p(10)}---{p(11)}       {p(12)}---{p(13)}---{p(14)}")
        print(f" |   |   |       |   |   |")
        print(f" |   |   {p(15)}---{p(16)}---{p(17)}   |   |")
        print(f" |   |       |       |   |")
        print(f" |   {p(18)}-------{p(19)}-------{p(20)}   |")
        print(f" |           |           |")
        print(f" {p(21)}----------{p(22)}----------{p(23)}")

    def display_board_with_numbers(self):
        def p(i):
            v = self.board[i]
            return v if v else '.'
        print()
        print("Board Layout (spot numbers for reference):")
        print()
        print(f" {p(0)}----------{p(1)}----------{p(2)}        0----------1----------2")
        print(f" |           |           |        |           |           |")
        print(f" |   {p(3)}-------{p(4)}-------{p(5)}   |        |   3-------4-------5   |")
        print(f" |   |       |       |   |        |   |       |       |   |")
        print(f" |   |   {p(6)}---{p(7)}---{p(8)}   |   |        |   |   6---7---8   |   |")
        print(f" |   |   |       |   |   |        |   |   |       |   |   |")
        print(f" {p(9)}---{p(10)}---{p(11)}       {p(12)}---{p(13)}---{p(14)}        9---10--11      12--13--14")
        print(f" |   |   |       |   |   |        |   |   |       |   |   |")
        print(f" |   |   {p(15)}---{p(16)}---{p(17)}   |   |        |   |   15--16--17  |   |")
        print(f" |   |       |       |   |        |   |       |       |   |")
        print(f" |   {p(18)}-------{p(19)}-------{p(20)}   |        |   18------19------20  |")
        print(f" |           |           |        |           |           |")
        print(f" {p(21)}----------{p(22)}----------{p(23)}        21---------22---------23")
        print()

    def get_state_for_agent(self, color):
        return {
            "board": self.board[:],
            "phase": self.phase,
            "your_color": color,
            "opponent_color": self.opponent(color),
            "pieces_in_hand": dict(self.pieces_in_hand),
            "pieces_on_board": dict(self.pieces_on_board),
            "move_count": self.move_count,
            "history": self.history[:],
        }
'''


# ============================================================
# Match runner code (play_game + main for agent-vs-agent)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

total_turns = 0


def play_game(game_num, match_stats):
    global total_turns
    game = SurroundMorrisGame()

    if random.random() < 0.5:
        b_agent_class = SurroundMorrisAgent_1
        w_agent_class = SurroundMorrisAgent_2
        b_name = "Agent-1"
        w_name = "Agent-2"
    else:
        b_agent_class = SurroundMorrisAgent_2
        w_agent_class = SurroundMorrisAgent_1
        b_name = "Agent-2"
        w_name = "Agent-1"

    print()
    print("=" * 60)
    print(f"GAME {game_num}")
    print(f"Agent-1: {AGENT1_INFO}")
    print(f"Agent-2: {AGENT2_INFO}")
    print(f"{b_name} plays B (Black), {w_name} plays W (White)")
    print("=" * 60)

    try:
        b_agent = b_agent_class(b_name, 'B')
    except Exception as e:
        print(f"{b_name} (B) init crash: {e}")
        match_stats[b_name]["other_crash"] += 1
        match_stats[w_name]["wins"] += 1
        match_stats[w_name]["points"] += 3
        match_stats[w_name]["score"] += 7
        match_stats[b_name]["losses"] += 1
        match_stats[b_name]["score"] -= 7
        return w_name

    try:
        w_agent = w_agent_class(w_name, 'W')
    except Exception as e:
        print(f"{w_name} (W) init crash: {e}")
        match_stats[w_name]["other_crash"] += 1
        match_stats[b_name]["wins"] += 1
        match_stats[b_name]["points"] += 3
        match_stats[b_name]["score"] += 7
        match_stats[w_name]["losses"] += 1
        match_stats[w_name]["score"] -= 7
        return b_name

    agents = {'B': b_agent, 'W': w_agent}
    names = {'B': b_name, 'W': w_name}

    def do_random_placement(color):
        legal = game.get_legal_placements(color)
        if legal:
            spot = random.choice(legal)
            captured = game.apply_placement(spot, color)
            return spot, captured
        return None, []

    def do_random_movement(color):
        legal = game.get_legal_movements(color)
        if legal:
            from_s, to_s = random.choice(legal)
            captured = game.apply_movement(from_s, to_s, color)
            return (from_s, to_s), captured
        return None, []

    result_desc = None
    game_over = False

    # --- Placement Phase ---
    placement_turn = 0
    while game.phase == 'placement' and not game_over:
        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        total_turns += 1
        placement_turn += 1

        state = game.get_state_for_agent(color)
        move = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = agent.make_move(state, None)
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            print(f"{agent_name} ({color}): TIMEOUT")
            match_stats[agent_name]["timeout"] += 1
            move = None
        except Exception as e:
            print(f"{agent_name} ({color}): CRASH '{str(e)[:80]}'")
            match_stats[agent_name]["make_move_crash"] += 1
            move = None

        valid = False
        if move is not None:
            if not isinstance(move, int):
                try:
                    move = int(move)
                except (ValueError, TypeError):
                    match_stats[agent_name]["invalid"] += 1
                    print(f"{agent_name} ({color}): INVALID OUTPUT '{move}'")
                    move = None

        if move is not None:
            ok, msg, error_code = game.validate_placement(move, color)
            if ok:
                valid = True
            else:
                match_stats[agent_name]["invalid"] += 1
                print(f"{agent_name} ({color}): INVALID placement at {move} - {msg}")
                move = None

        if valid:
            captured = game.apply_placement(move, color)
            cap_str = f" captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): placement at {move}{cap_str}")
            match_stats[agent_name]["captures"] += len(captured)
        else:
            spot, captured = do_random_placement(color)
            if spot is not None:
                cap_str = f" captured {captured}" if captured else ""
                print(f"{agent_name} ({color}): random placement at {spot}{cap_str}")
                match_stats[agent_name]["captures"] += len(captured)

        # Check elimination after move (self-harm priority: mover checked first)
        game_over, result_desc = game.check_elimination()
        if game_over:
            break

        game.check_phase_transition()
        game.current_player = game.opponent(color)

    # --- Movement Phase ---
    if game.phase == 'movement' and not game_over:
        print()
        print("--- MOVEMENT PHASE ---")

    while game.phase == 'movement' and not game_over:
        # Record history and check repetition BEFORE move
        game.record_history()
        game_over, result_desc = game.check_repetition()
        if game_over:
            break

        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        total_turns += 1

        # Check stalemate before move — stuck player loses
        legal_moves = game.get_legal_movements(color)
        if not legal_moves:
            opp_color = game.opponent(color)
            print(f"{agent_name} ({color}): no legal moves, {opp_color} wins by Mate")
            match_stats[agent_name]["stalemate"] += 1
            result_desc = f"{opp_color} wins by Mate ({color} has no legal moves)"
            game_over = True
            break

        state = game.get_state_for_agent(color)
        move = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = agent.make_move(state, None)
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            print(f"{agent_name} ({color}): TIMEOUT")
            match_stats[agent_name]["timeout"] += 1
            move = None
        except Exception as e:
            print(f"{agent_name} ({color}): CRASH '{str(e)[:80]}'")
            match_stats[agent_name]["make_move_crash"] += 1
            move = None

        valid = False
        if move is not None:
            if not isinstance(move, (tuple, list)) or len(move) != 2:
                match_stats[agent_name]["invalid"] += 1
                print(f"{agent_name} ({color}): INVALID OUTPUT '{move}'")
                move = None

        if move is not None:
            try:
                from_spot, to_spot = int(move[0]), int(move[1])
            except (ValueError, TypeError):
                match_stats[agent_name]["invalid"] += 1
                print(f"{agent_name} ({color}): INVALID non-int move {move}")
                move = None

        if move is not None:
            ok, msg, error_code = game.validate_movement(from_spot, to_spot, color)
            if ok:
                valid = True
            else:
                match_stats[agent_name]["invalid"] += 1
                print(f"{agent_name} ({color}): INVALID move {from_spot}->{to_spot} - {msg}")
                move = None

        if valid:
            captured = game.apply_movement(from_spot, to_spot, color)
            cap_str = f" captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): move {from_spot}->{to_spot}{cap_str}")
            match_stats[agent_name]["captures"] += len(captured)
        else:
            mv, captured = do_random_movement(color)
            if mv:
                cap_str = f" captured {captured}" if captured else ""
                print(f"{agent_name} ({color}): random move {mv[0]}->{mv[1]}{cap_str}")
                match_stats[agent_name]["captures"] += len(captured)
            else:
                opp_color = game.opponent(color)
                print(f"{agent_name} ({color}): no legal moves after fallback, {opp_color} wins by Mate")
                match_stats[agent_name]["stalemate"] += 1
                result_desc = f"{opp_color} wins by Mate ({color} has no legal moves)"
                game_over = True
                break

        # Check game end AFTER move: elimination first, then turn limit
        game.move_count += 1

        game_over, result_desc = game.check_elimination()
        if not game_over:
            game_over, result_desc = game.check_turn_limit()

        if game_over:
            break

        game.current_player = game.opponent(color)

    if not result_desc:
        result_desc = "Game ended unexpectedly"

    print()
    game.display_board()
    print(f"Pieces: B={game.pieces_on_board['B']} W={game.pieces_on_board['W']}")
    print(f"GAME {game_num} ENDED: {result_desc}")

    # Determine winner/loser and scores (loser gets negative)
    winner_score = 0
    loser_score = 0
    winner_color = None

    if "wins" in result_desc:
        winner_color = result_desc[0]
        loser_color = game.opponent(winner_color)
        winner = names[winner_color]
        loser = names[loser_color]

        if "Mate" in result_desc:
            winner_score = 7
            loser_score = -7
        else:
            winner_score = game.pieces_on_board[winner_color]
            loser_score = -game.pieces_on_board[winner_color]

    elif "Draw" in result_desc:
        winner_color = None
        winner = "DRAW"
        winner_score = 0
        loser_score = 0
    else:
        winner_color = None
        winner = "DRAW"
        winner_score = 0
        loser_score = 0

    if winner != "DRAW":
        print(f"{winner_color} ({winner}) wins with score of {winner_score}")
    else:
        print(f"Game ended in a DRAW")

    print(f"Winner: {winner}")

    if winner != "DRAW":
        match_stats[winner]["wins"] += 1
        match_stats[winner]["points"] += 3
        match_stats[winner]["score"] += winner_score
        match_stats[loser]["losses"] += 1
        match_stats[loser]["score"] += loser_score
    else:
        match_stats["Agent-1"]["draws"] += 1
        match_stats["Agent-1"]["points"] += 1
        match_stats["Agent-1"]["score"] += winner_score
        match_stats["Agent-2"]["draws"] += 1
        match_stats["Agent-2"]["points"] += 1
        match_stats["Agent-2"]["score"] += loser_score

    print("=" * 60)
    sys.stdout.flush()

    return winner


def main():
    match_stats = {
        "Agent-1": {"wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
                     "make_move_crash": 0, "other_crash": 0, "crash": 0,
                     "timeout": 0, "invalid": 0, "captures": 0, "stalemate": 0},
        "Agent-2": {"wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
                     "make_move_crash": 0, "other_crash": 0, "crash": 0,
                     "timeout": 0, "invalid": 0, "captures": 0, "stalemate": 0},
    }

    for i in range(NUM_GAMES):
        play_game(i + 1, match_stats)
        sys.stdout.flush()

    print("\nFinal Results")
    print(f"Agent 1 ({AGENT1_INFO}) Wins: {match_stats['Agent-1']['wins']} times")
    print(f"Agent 2 ({AGENT2_INFO}) Wins: {match_stats['Agent-2']['wins']} times")
    print("Points:")
    print(f"Agent 1: {match_stats['Agent-1']['points']}")
    print(f"Agent 2: {match_stats['Agent-2']['points']}")
    print("Scores:")
    print(f"Agent 1: {match_stats['Agent-1']['score']}")
    print(f"Agent 2: {match_stats['Agent-2']['score']}")

    print(f"RESULT:Agent-1={match_stats['Agent-1']['points']},Agent-2={match_stats['Agent-2']['points']}")
    print(f"SCORE:Agent-1={match_stats['Agent-1']['score']},Agent-2={match_stats['Agent-2']['score']}")
    print(f"WINS:Agent-1={match_stats['Agent-1']['wins']},Agent-2={match_stats['Agent-2']['wins']}")
    print(f"DRAWS:{match_stats['Agent-1']['draws']}")
    # Aggregate crash stat for backward compatibility
    for agent_key in ["Agent-1", "Agent-2"]:
        match_stats[agent_key]["crash"] = match_stats[agent_key]["make_move_crash"] + match_stats[agent_key]["other_crash"]

    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 make_move_crash: {match_stats['Agent-1']['make_move_crash']}")
    print(f"Agent-2 make_move_crash: {match_stats['Agent-2']['make_move_crash']}")
    print(f"Agent-1 other_crash: {match_stats['Agent-1']['other_crash']}")
    print(f"Agent-2 other_crash: {match_stats['Agent-2']['other_crash']}")
    print(f"Agent-1 crash (total): {match_stats['Agent-1']['crash']}")
    print(f"Agent-2 crash (total): {match_stats['Agent-2']['crash']}")
    print(f"Agent-1 Timeouts: {match_stats['Agent-1']['timeout']}")
    print(f"Agent-2 Timeouts: {match_stats['Agent-2']['timeout']}")
    print(f"Agent-1 Invalid: {match_stats['Agent-1']['invalid']}")
    print(f"Agent-2 Invalid: {match_stats['Agent-2']['invalid']}")
    print(f"Agent-1 Captures: {match_stats['Agent-1']['captures']}")
    print(f"Agent-2 Captures: {match_stats['Agent-2']['captures']}")
    print(f"Agent-1 Stalemates: {match_stats['Agent-1']['stalemate']}")
    print(f"Agent-2 Stalemates: {match_stats['Agent-2']['stalemate']}")
    print(f"Total Turns: {total_turns}")
    print(f"STATS:Agent-1={match_stats['Agent-1']},Agent-2={match_stats['Agent-2']}")


if __name__ == "__main__":
    main()
'''


# ============================================================
# Human play mode code
# ============================================================
HUMAN_PLAY_CODE = r'''
import random
import datetime
import os


class HumanAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        game = SurroundMorrisGame()
        game.board = state["board"][:]
        game.phase = state["phase"]
        game.pieces_in_hand = state["pieces_in_hand"].copy()
        game.pieces_on_board = state["pieces_on_board"].copy()

        while True:
            print()
            print("=" * 60)
            print(f"{self.name}'s turn ({self.color})")
            print(f"Phase: {state['phase'].upper()}")
            print("=" * 60)

            game.display_board_with_numbers()

            print(f"Pieces on board: B={state['pieces_on_board']['B']} W={state['pieces_on_board']['W']}")
            print(f"Pieces in hand: B={state['pieces_in_hand']['B']} W={state['pieces_in_hand']['W']}")
            print()

            if feedback:
                print(f"Previous error: {feedback.get('error_message', 'Unknown')}")
                print()

            if state["phase"] == "placement":
                print("Enter a spot number (0-23) to place your piece:")
                try:
                    move = input("> ").strip()
                    spot = int(move)
                    ok, msg, _ = game.validate_placement(spot, self.color)
                    if ok:
                        return spot
                    else:
                        print(f"Invalid: {msg}")
                except ValueError:
                    print("Please enter a valid number.")
            else:
                print("Enter move as 'from to' (e.g., '3 4'):")
                try:
                    move = input("> ").strip()
                    parts = move.split()
                    if len(parts) != 2:
                        print("Please enter two numbers separated by space.")
                        continue
                    from_spot, to_spot = int(parts[0]), int(parts[1])
                    ok, msg, _ = game.validate_movement(from_spot, to_spot, self.color)
                    if ok:
                        return (from_spot, to_spot)
                    else:
                        print(f"Invalid: {msg}")
                except ValueError:
                    print("Please enter valid numbers.")


class RandomAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        if state["phase"] == "placement":
            legal = [s for s in range(24) if state["board"][s] == '']
            return random.choice(legal) if legal else 0
        else:
            moves = []
            for f in range(24):
                if state["board"][f] != self.color:
                    continue
                for t in ADJACENCY[f]:
                    if state["board"][t] == '':
                        moves.append((f, t))
            return random.choice(moves) if moves else None


MAX_TURNS = 200

MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}


if __name__ == "__main__":
    mode_title = MODE_TITLES.get(GAME_MODE, GAME_MODE)

    print("=" * 60)
    print(f"SURROUND MORRIS - {mode_title}")
    print("=" * 60)
    print()
    print("Capture Rule: A piece is captured when it has zero empty")
    print("neighbors AND more opponent neighbors than friendly neighbors.")
    print()

    if GAME_MODE == "humanvsbot":
        if random.random() < 0.5:
            agent_b = HumanAgent("Human", "B")
            agent_w = RandomAgent("Bot", "W")
            print("You are B (Black, moves first)")
        else:
            agent_b = RandomAgent("Bot", "B")
            agent_w = HumanAgent("Human", "W")
            print("You are W (White, moves second)")

    elif GAME_MODE == "humanvshuman":
        agent_b = HumanAgent("Player 1", "B")
        agent_w = HumanAgent("Player 2", "W")
        print("Player 1 is B (Black, moves first)")
        print("Player 2 is W (White, moves second)")

    elif GAME_MODE == "humanvsagent":
        if random.random() < 0.5:
            agent_b = HumanAgent("Human", "B")
            agent_w = SurroundMorrisAgent_1("Agent", "W")
            print("You are B (Black, moves first)")
        else:
            agent_b = SurroundMorrisAgent_1("Agent", "B")
            agent_w = HumanAgent("Human", "W")
            print("You are W (White, moves second)")

    agents = {"B": agent_b, "W": agent_w}
    names = {"B": agents["B"].name, "W": agents["W"].name}

    game = SurroundMorrisGame()
    result_desc = None
    game_over = False

    print("--- PLACEMENT PHASE ---")
    print("Each player places 7 pieces.")

    while game.phase == 'placement' and not game_over:
        color = game.current_player
        agent = agents[color]
        agent_name = names[color]

        state = game.get_state_for_agent(color)
        move = agent.make_move(state, None)

        ok, msg, _ = game.validate_placement(move, color)
        if not ok:
            print(f"{agent_name} ({color}): Invalid placement {move} - {msg}")
            if not isinstance(agent, HumanAgent):
                legal = game.get_legal_placements(color)
                if legal:
                    move = random.choice(legal)
                    captured = game.apply_placement(move, color)
                    cap_str = f" - captured {captured}" if captured else ""
                    print(f"{agent_name} ({color}): placed at {move}{cap_str}")
        else:
            captured = game.apply_placement(move, color)
            cap_str = f" - captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): placed at {move}{cap_str}")

        game_over, result_desc = game.check_elimination()
        if game_over:
            break

        game.check_phase_transition()
        game.current_player = game.opponent(color)

    print()
    print("=" * 60)
    print("--- MOVEMENT PHASE ---")
    print("=" * 60)
    game.display_board_with_numbers()

    while game.phase == 'movement' and not game_over:
        game.record_history()
        game_over, result_desc = game.check_repetition()
        if game_over:
            break

        color = game.current_player
        agent = agents[color]
        agent_name = names[color]

        legal_moves = game.get_legal_movements(color)
        if not legal_moves:
            opp_color = game.opponent(color)
            print(f"{agent_name} ({color}): no legal moves, {opp_color} wins by Mate")
            game_over = True
            result_desc = f"{opp_color} wins by Mate ({color} has no legal moves)"
            break

        state = game.get_state_for_agent(color)
        move = agent.make_move(state, None)

        if move is None:
            print(f"{agent_name} ({color}): no move returned")
            continue

        from_spot, to_spot = move
        ok, msg, _ = game.validate_movement(from_spot, to_spot, color)
        if not ok:
            print(f"{agent_name} ({color}): Invalid move {from_spot}->{to_spot} - {msg}")
            if not isinstance(agent, HumanAgent) and legal_moves:
                from_spot, to_spot = random.choice(legal_moves)
                captured = game.apply_movement(from_spot, to_spot, color)
                cap_str = f" - captured {captured}" if captured else ""
                print(f"{agent_name} ({color}): moved {from_spot}->{to_spot}{cap_str}")
        else:
            captured = game.apply_movement(from_spot, to_spot, color)
            cap_str = f" - captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): moved {from_spot}->{to_spot}{cap_str}")

        game.move_count += 1

        game_over, result_desc = game.check_elimination()
        if not game_over:
            game_over, result_desc = game.check_turn_limit()

        if game_over:
            break

        game.current_player = game.opponent(color)

    print()
    print("=" * 60)
    game.display_board_with_numbers()
    print(f"Pieces: B={game.pieces_on_board['B']} W={game.pieces_on_board['W']}")

    winner_name = "DRAW"
    winner_color = None

    if result_desc and "wins" in result_desc:
        winner_color = result_desc[0]
        winner_name = names[winner_color]

        if "Mate" in result_desc:
            score = 7
        else:
            score = game.pieces_on_board[winner_color]

        print(f"GAME ENDED: {winner_color} ({winner_name}) wins with score of {score}")
    else:
        print(f"GAME ENDED: {result_desc if result_desc else 'Draw'}")

    print()
    print("Thanks for playing!")

    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"surround_morris_{GAME_MODE}_{ts}.txt"
        log_dir = "."
        if os.path.exists("../results/surround_morris"):
            log_dir = "../results/surround_morris"
        elif os.path.exists("results/surround_morris"):
            log_dir = "results/surround_morris"
        filepath = os.path.join(log_dir, filename)
        with open(filepath, "w") as f:
            f.write(f"Surround Morris Game - {mode_title}\n")
            f.write(f"Date: {datetime.datetime.now()}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Result: {result_desc}\n")
            if winner_color:
                f.write(f"Winner: {winner_name} ({winner_color})\n")
            else:
                f.write("Winner: DRAW\n")
            f.write(f"\nPieces B: {game.pieces_on_board['B']}\n")
            f.write(f"Pieces W: {game.pieces_on_board['W']}\n")
            f.write(f"Total Moves: {game.move_count}\n")
        print(f"\nGame report saved to: {filepath}")
    except Exception as e:
        print(f"Could not save game report: {e}")
'''


def find_model_folder(pattern: str) -> str | None:
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

    # Exact match first (matchmaker passes full folder names)
    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

    # Substring fallback for interactive CLI use
    matches = [
        d.name for d in AGENTS_DIR.iterdir()
        if d.is_dir() and pattern.lower() in d.name.lower()
    ]

    if not matches:
        logger.error("No model folder matches pattern '%s'", pattern)
        return None

    if len(matches) > 1:
        return ModelAPI.resolve_model_interactive(pattern, matches, context="folder")

    return matches[0]


def get_available_runs(model_folder: str, game: str) -> list[int]:
    model_dir = AGENTS_DIR / model_folder
    runs = []
    pattern = re.compile(rf"^{re.escape(game)}_(\d+)\.py$")

    for file in model_dir.glob(f"{game}_*.py"):
        match = pattern.match(file.name)
        if match:
            runs.append(int(match.group(1)))

    return sorted(runs)


def load_stored_agent(
    model_folder: str, game: str, run: int, agent_idx: int
) -> tuple[str, str]:
    agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"

    if not agent_file.exists():
        logger.error("Agent file not found: %s", agent_file)
        return "", ""

    content = agent_file.read_text()
    lines = content.split("\n")

    code_start = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line:
            if in_docstring:
                code_start = i + 1
                break
            else:
                in_docstring = True

    code_lines = lines[code_start:]

    imports = []
    class_start_idx = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()

        if stripped.startswith("class SurroundMorrisAgent"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No SurroundMorrisAgent class found in %s", agent_file)
        return "", ""

    class_lines = []
    base_indent = 0

    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()

        if i == class_start_idx:
            class_lines.append(line)
            base_indent = len(line) - len(line.lstrip())
            continue

        if not stripped or stripped.startswith("#"):
            class_lines.append(line)
            continue

        current_indent = len(line) - len(line.lstrip())

        if current_indent <= base_indent:
            break

        class_lines.append(line)

    agent_code = "\n".join(class_lines)

    agent_code = re.sub(
        r"\bSurroundMorrisAgent\b", f"SurroundMorrisAgent_{agent_idx}", agent_code
    )

    return agent_code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs


def build_game_code(
    agent1_code: str,
    agent2_code: str,
    extra_imports: str,
    num_games: int,
    move_timeout: float,
    max_turns: int,
    agent1_info: str,
    agent2_info: str,
) -> str:
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "from collections import Counter\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"MAX_TURNS = {max_turns}\n"
        f"NUM_GAMES = {num_games}\n"
        f'AGENT1_INFO = "{agent1_info}"\n'
        f'AGENT2_INFO = "{agent2_info}"\n'
    )

    return "\n\n".join([
        header,
        extra_imports,
        agent1_code,
        agent2_code,
        GAME_ENGINE_CODE,
        MATCH_RUNNER_CODE,
    ])


def build_human_game_code(
    mode: str, agent_code: str = "", agent_imports: str = ""
) -> str:
    mode_header = f'GAME_MODE = "{mode}"\n'
    parts = [mode_header]
    if mode == "humanvsagent" and agent_imports:
        parts.append(agent_imports)
    if mode == "humanvsagent" and agent_code:
        parts.append(agent_code)
    parts.append(GAME_ENGINE_CODE)
    parts.append(HUMAN_PLAY_CODE)
    return "\n\n".join(parts)


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 600
) -> dict:
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"surround_morris_match_{match_id}_{temp_id}.py"
    )

    try:
        with open(temp_file, "w") as f:
            f.write(game_code)

        result = subprocess.run(
            ["python", temp_file], capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": False,
                "agent1_score": 0,
                "agent2_score": 0,
                "error": result.stderr[:500],
            }

        match = re.search(
            r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout
        )

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            wins_match = re.search(
                r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout
            )
            draws_match = re.search(r"DRAWS:(\d+)", result.stdout)
            score_match = re.search(
                r"SCORE:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", result.stdout
            )

            agent1_wins = int(wins_match.group(1)) if wins_match else 0
            agent2_wins = int(wins_match.group(2)) if wins_match else 0
            draws = int(draws_match.group(1)) if draws_match else 0
            agent1_points = int(float(match.group(1))) if match else 0
            agent2_points = int(float(match.group(2))) if match else 0
            agent1_score = float(score_match.group(1)) if score_match else 0.0
            agent2_score = float(score_match.group(2)) if score_match else 0.0

            log_lines = []
            for line in result.stdout.splitlines():
                if line.startswith((
                    "Agent-1:", "Agent-2:", "GAME ", "Game ", "Winner:",
                    "Running Total", "==========", "--- MOVEMENT",
                    "Final", "Scores:", "Agent 1", "Agent 2",
                    "CRASH", "RESULT", "SCORE", "WINS", "DRAWS",
                    "Pieces:", "Points:",
                )) or "ENDED" in line or line.strip() == "":
                    log_lines.append(line)

            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": True,
                "agent1_score": agent1_score,
                "agent2_score": agent2_score,
                "agent1_wins": agent1_wins,
                "agent2_wins": agent2_wins,
                "agent1_points": agent1_points,
                "agent2_points": agent2_points,
                "draws": draws,
                "error": None,
                "stats_block": stats_block,
                "log": "\n".join(log_lines),
            }

        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_score": 0,
            "agent2_score": 0,
            "error": "Could not parse results:\n" + result.stdout[:200],
        }

    except Exception as e:
        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_score": 0,
            "agent2_score": 0,
            "error": str(e),
        }
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str, match_id: int, run_ids: tuple[int, int]
) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run Surround Morris matches")
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1[:run1:run2] model2[:run3:run4]",
    )
    human_group = parser.add_mutually_exclusive_group()
    human_group.add_argument(
        "--humanvsbot", action="store_true",
        help="Play interactively against a random bot",
    )
    human_group.add_argument(
        "--humanvshuman", action="store_true",
        help="Two humans play at the same terminal",
    )
    human_group.add_argument(
        "--humanvsagent", action="store_true",
        help="Play against a stored agent (requires --agent with 1 spec)",
    )
    args = parser.parse_args()

    human_mode = None
    if args.humanvsbot:
        human_mode = "humanvsbot"
    elif args.humanvshuman:
        human_mode = "humanvshuman"
    elif args.humanvsagent:
        human_mode = "humanvsagent"

    if human_mode:
        if human_mode == "humanvsagent":
            if not args.agent or len(args.agent) != 1:
                print("ERROR: --humanvsagent requires exactly 1 --agent spec.")
                print("Example: --humanvsagent --agent mistral:1")
                sys.exit(1)
            model_pattern, runs = parse_agent_spec(args.agent[0])
            folder = find_model_folder(model_pattern)
            if not folder:
                sys.exit(1)
            if not runs:
                runs = get_available_runs(folder, GAME_NAME)
            if not runs:
                print(f"ERROR: No runs found for {folder}/{GAME_NAME}")
                sys.exit(1)
            agent_code, agent_imports = load_stored_agent(
                folder, GAME_NAME, runs[0], 1
            )
            if not agent_code:
                print(f"ERROR: Failed to load agent from {folder}")
                sys.exit(1)
            game_code = build_human_game_code(
                "humanvsagent", agent_code, agent_imports
            )
        elif args.agent:
            print("ERROR: --agent is not used with --humanvsbot or --humanvshuman.")
            sys.exit(1)
        else:
            game_code = build_human_game_code(human_mode)

        temp_file = os.path.join(
            tempfile.gettempdir(),
            f"surround_morris_{human_mode}_{uuid.uuid4().hex[:8]}.py",
        )
        try:
            with open(temp_file, "w") as f:
                f.write(game_code)
            subprocess.run(
                ["python", temp_file],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
            )
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return

    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        print("Example: --agent mistral:1 gpt-5-mini:1")
        sys.exit(1)

    model1_pattern, runs1 = parse_agent_spec(args.agent[0])
    model2_pattern, runs2 = parse_agent_spec(args.agent[1])

    folder1 = find_model_folder(model1_pattern)
    folder2 = find_model_folder(model2_pattern)

    if not folder1 or not folder2:
        sys.exit(1)

    if not runs1:
        runs1 = get_available_runs(folder1, GAME_NAME)
    if not runs2:
        runs2 = get_available_runs(folder2, GAME_NAME)

    num_matches = min(len(runs1), len(runs2))
    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("SURROUND MORRIS MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    agent_suffix = f"{folder1}_vs_{folder2}"
    log_f = RESULTS_DIR / f"{ts}_{agent_suffix}_match.txt"

    match_tasks = []

    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]

        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1)
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2)

        if not code1 or not code2:
            print(f"  FAILED to load match {i + 1}")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        agent1_info = f"{folder1}:{run1}"
        agent2_info = f"{folder2}:{run2}"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH,
            MOVE_TIME_LIMIT, MAX_TURNS_PER_GAME, agent1_info, agent2_info,
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    total1, total2 = 0.0, 0.0
    total_pts1, total_pts2 = 0, 0

    with open(log_f, "w") as f:
        f.write(f"Surround Morris Match - {ts}\n")
        f.write("=" * 60 + "\n\n")

        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
            if result["success"]:
                s1, s2 = result["agent1_score"], result["agent2_score"]
                p1 = result.get("agent1_points", 0)
                p2 = result.get("agent2_points", 0)
                total1 += s1
                total2 += s2
                total_pts1 += p1
                total_pts2 += p2
                status = f"Result: Pts {p1}-{p2}, Score {s1:.1f}-{s2:.1f}"
                game_log = result.get("log", "")
                if game_log:
                    status += f"\n{game_log}\n"
                if result.get("stats_block"):
                    status += (
                        f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
                    )
            else:
                status = f"FAILED: {result.get('error', 'Unknown')}"

            print(f"  Match {match_id}: {status}")
            f.write(f"Match {match_id}: {status}\n")
            if result.get("stats_block"):
                f.write(
                    f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
                )
                f.write("-" * 60 + "\n\n")

    runs1_str = ",".join(str(r) for r in runs1)
    runs2_str = ",".join(str(r) for r in runs2)
    print("\nFINAL RESULTS:")
    print(f"  {folder1}:{runs1_str}: Pts {total_pts1}, Score {total1:.1f}")
    print(f"  {folder2}:{runs2_str}: Pts {total_pts2}, Score {total2:.1f}")
    print(f"\nLogs saved to: {log_f}")

    # Update global scoreboard
    scoreboard_path = Path(__file__).parent.parent / "scoreboard" / "A8-scoreboard.txt"

    for result in results:
        if not result["success"]:
            continue

        run1 = result["agent1_run_id"]
        run2 = result["agent2_run_id"]
        agent1_key = f"{folder1}:{run1}"
        agent2_key = f"{folder2}:{run2}"

        a1_wins = result.get("agent1_wins", 0)
        a2_wins = result.get("agent2_wins", 0)
        match_draws = result.get("draws", 0)

        update_scoreboard(
            scoreboard_path,
            agent1_key,
            games_played=NUM_GAMES_PER_MATCH,
            wins=a1_wins,
            losses=a2_wins,
            draws=match_draws,
            score=result["agent1_score"],
            points=result.get("agent1_points", 0),
        )
        update_scoreboard(
            scoreboard_path,
            agent2_key,
            games_played=NUM_GAMES_PER_MATCH,
            wins=a2_wins,
            losses=a1_wins,
            draws=match_draws,
            score=result["agent2_score"],
            points=result.get("agent2_points", 0),
        )

    print(f"Scoreboard updated: {scoreboard_path}")


if __name__ == "__main__":
    asyncio.run(main_async())