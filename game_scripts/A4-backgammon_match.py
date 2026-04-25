"""
Backgammon Match Runner: Orchestrates head-to-head matches for A4-Backgammon.

Standard backgammon: 24 points, 15 checkers per side, two six-sided dice.
Each subprocess invocation plays one race-to-5 in-game points (Single = 1,
Gammon = 2, turn-limit Draw = 0.5/0.5). League scoring: 3/1/0 for match
win/draw/loss; tie-break score = ±(in-game-point diff).
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

sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard
from agent_loader import load_stored_agent, consolidate_imports, COMMON_HEADER_IMPORTS

logger = setup_logging(__name__)

load_dotenv()

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

try:
    MATCH_TIME_LIMIT = int(os.getenv("MATCH_TIME_LIMIT", "900"))
except (ValueError, TypeError):
    MATCH_TIME_LIMIT = 900

MAX_TURNS_PER_GAME = 300
POINTS_TO_WIN_MATCH = 5
MAX_GAMES_PER_MATCH = 30

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "backgammon"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A4-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"
GAME_NAME = "A4-Backgammon"


# ============================================================
# Shared game engine code (used by match runner and human modes)
# ============================================================
GAME_ENGINE_CODE = r'''
class BackgammonGame:
    """Standard backgammon engine. Absolute point indices 0-23.

    Board representation: list of 24 ints. Positive = White checker count,
    negative = Black checker count, 0 = empty. White moves toward index 0
    (decreasing) and bears off from points 0-5. Black moves toward index 23
    (increasing) and bears off from points 18-23.
    """

    NUM_POINTS = 24
    CHECKERS_PER_PLAYER = 15

    def __init__(self):
        self.board = [0] * 24
        self.board[5] = 5
        self.board[7] = 3
        self.board[12] = 5
        self.board[23] = 2
        self.board[18] = -5
        self.board[16] = -3
        self.board[11] = -5
        self.board[0] = -2

        self.bar = {'W': 0, 'B': 0}
        self.borne_off = {'W': 0, 'B': 0}
        self.current_player = None
        self.turn_count = 0

    def opponent(self, color):
        return 'W' if color == 'B' else 'B'

    def color_at(self, point):
        v = self.board[point]
        if v > 0:
            return 'W'
        if v < 0:
            return 'B'
        return None

    def count_at(self, point):
        return abs(self.board[point])

    def is_in_home(self, color, point):
        if color == 'W':
            return 0 <= point <= 5
        return 18 <= point <= 23

    def all_in_home(self, color):
        if self.bar[color] > 0:
            return False
        if color == 'W':
            for i in range(6, 24):
                if self.board[i] > 0:
                    return False
        else:
            for i in range(0, 18):
                if self.board[i] < 0:
                    return False
        return True

    def _highest_in_home(self, color):
        if color == 'W':
            for i in range(5, -1, -1):
                if self.board[i] > 0:
                    return i
        else:
            for i in range(18, 24):
                if self.board[i] < 0:
                    return i
        return None

    def _can_land(self, color, point):
        v = self.board[point]
        if v == 0:
            return True
        if color == 'W':
            return v > 0 or v == -1
        return v < 0 or v == 1

    def get_legal_sub_moves(self, color, dice):
        """All legal SINGLE sub-moves given the dice values (no chaining).
        Returns list of (from, to) tuples. If color has bar checkers, only
        bar-entry sub-moves are returned (bar priority).
        """
        moves = []
        seen = set()
        die_set = set(dice)

        if self.bar[color] > 0:
            for d in die_set:
                entry = 24 - d if color == 'W' else d - 1
                if 0 <= entry <= 23 and self._can_land(color, entry):
                    sub = ('bar', entry)
                    if sub not in seen:
                        seen.add(sub)
                        moves.append(sub)
            return moves

        all_in = self.all_in_home(color)
        highest = self._highest_in_home(color) if all_in else None

        for from_p in range(24):
            v = self.board[from_p]
            if (color == 'W' and v <= 0) or (color == 'B' and v >= 0):
                continue
            for d in die_set:
                to_p = from_p - d if color == 'W' else from_p + d

                if (color == 'W' and to_p < 0) or (color == 'B' and to_p > 23):
                    if not all_in:
                        continue
                    exact = (color == 'W' and to_p == -1) or (color == 'B' and to_p == 24)
                    if exact:
                        sub = (from_p, 'off')
                    else:
                        if from_p != highest:
                            continue
                        sub = (from_p, 'off')
                    if sub not in seen:
                        seen.add(sub)
                        moves.append(sub)
                elif 0 <= to_p <= 23:
                    if self._can_land(color, to_p):
                        sub = (from_p, to_p)
                        if sub not in seen:
                            seen.add(sub)
                            moves.append(sub)
        return moves

    def _apply_sub_move(self, color, sub_move):
        from_p, to_p = sub_move
        sign = 1 if color == 'W' else -1
        opp = self.opponent(color)
        hit = False

        if from_p == 'bar':
            self.bar[color] -= 1
        else:
            self.board[from_p] -= sign

        if to_p == 'off':
            self.borne_off[color] += 1
        else:
            if self.board[to_p] == -sign:
                self.board[to_p] = 0
                self.bar[opp] += 1
                hit = True
            self.board[to_p] += sign

        return (from_p, to_p, hit)

    def _undo_sub_move(self, color, undo_info):
        from_p, to_p, hit = undo_info
        sign = 1 if color == 'W' else -1
        opp = self.opponent(color)

        if to_p == 'off':
            self.borne_off[color] -= 1
        else:
            self.board[to_p] -= sign
            if hit:
                self.bar[opp] -= 1
                self.board[to_p] = -sign

        if from_p == 'bar':
            self.bar[color] += 1
        else:
            self.board[from_p] += sign

    def max_dice_usable(self, color, dice):
        """Maximum number of dice from `dice` that can be played in sequence."""
        if not dice:
            return 0
        best = 0
        seen_d = set()
        for d in dice:
            if d in seen_d:
                continue
            seen_d.add(d)
            for sub in self.get_legal_sub_moves(color, [d]):
                undo = self._apply_sub_move(color, sub)
                new_dice = list(dice)
                new_dice.remove(d)
                sub_max = 1 + self.max_dice_usable(color, new_dice)
                self._undo_sub_move(color, undo)
                if sub_max > best:
                    best = sub_max
                    if best == len(dice):
                        return best
        return best

    def _find_die_for_sub(self, color, sub_move, remaining_dice):
        """Return a die value from remaining_dice that legalizes this sub-move.
        For bear-off, prefers exact distance; falls back to overshoot.
        """
        from_p, to_p = sub_move

        if to_p == 'off':
            exact_d = (from_p + 1) if color == 'W' else (24 - from_p)
            if exact_d in remaining_dice and sub_move in self.get_legal_sub_moves(color, [exact_d]):
                return exact_d
            for d in sorted(set(remaining_dice)):
                if d > exact_d and sub_move in self.get_legal_sub_moves(color, [d]):
                    return d
            return None

        if from_p == 'bar':
            d = (24 - to_p) if color == 'W' else (to_p + 1)
            if d in remaining_dice and sub_move in self.get_legal_sub_moves(color, [d]):
                return d
            return None

        d = (from_p - to_p) if color == 'W' else (to_p - from_p)
        if 1 <= d <= 6 and d in remaining_dice and sub_move in self.get_legal_sub_moves(color, [d]):
            return d
        return None

    def validate_and_apply_turn(self, color, dice, sequence, max_usable=None):
        """Validate the agent's sub-move sequence; if valid, apply it.
        Returns (success: bool, error_msg: str, hits: int).
        """
        if max_usable is None:
            max_usable = self.max_dice_usable(color, dice)

        if not isinstance(sequence, list):
            return False, "Move must be a list", 0

        if len(sequence) != max_usable:
            return False, f"Sequence length {len(sequence)} != required {max_usable}", 0

        if max_usable == 0:
            return True, "", 0

        remaining = list(dice)
        applied = []
        hits = 0

        for i, sub in enumerate(sequence):
            if not isinstance(sub, (tuple, list)) or len(sub) != 2:
                self._rollback(color, applied)
                return False, f"Sub-move {i} not a 2-tuple", 0
            from_p, to_p = sub[0], sub[1]
            try:
                if from_p != 'bar':
                    from_p = int(from_p)
                if to_p != 'off':
                    to_p = int(to_p)
            except (ValueError, TypeError):
                self._rollback(color, applied)
                return False, f"Sub-move {i} has invalid types: {sub}", 0
            sub_norm = (from_p, to_p)

            die = self._find_die_for_sub(color, sub_norm, remaining)
            if die is None:
                self._rollback(color, applied)
                return False, f"Sub-move {sub_norm} not legal with remaining dice {remaining}", 0
            undo = self._apply_sub_move(color, sub_norm)
            if undo[2]:
                hits += 1
            applied.append(undo)
            remaining.remove(die)

        return True, "", hits

    def _rollback(self, color, applied):
        for undo in reversed(applied):
            self._undo_sub_move(color, undo)

    def is_game_over(self):
        if self.borne_off['W'] == 15:
            return True, 'W', ('gammon' if self.borne_off['B'] == 0 else 'single')
        if self.borne_off['B'] == 15:
            return True, 'B', ('gammon' if self.borne_off['W'] == 0 else 'single')
        return False, None, None

    def display_board(self, prefix='BOARD:'):
        TOP_LEFT = list(range(12, 18))
        TOP_RIGHT = list(range(18, 24))
        BOT_LEFT = list(range(11, 5, -1))
        BOT_RIGHT = list(range(5, -1, -1))

        def cell(p, row):
            v = self.board[p]
            count = abs(v)
            if v == 0 or row >= count:
                return ' . '
            ch = 'W' if v > 0 else 'B'
            if row == 4 and count > 5:
                return f'{count:>2}{ch}'[-3:]
            return f' {ch} '

        def fmt_labels(left, right):
            l = ' '.join(f'{p:>2}' for p in left)
            r = ' '.join(f'{p:>2}' for p in right)
            return f' {l}  |  {r}'

        sep = '-' * 41

        print(f'{prefix}{fmt_labels(TOP_LEFT, TOP_RIGHT)}')
        print(f'{prefix} {sep}')
        for row in range(5):
            left = ''.join(cell(p, row) for p in TOP_LEFT)
            right = ''.join(cell(p, row) for p in TOP_RIGHT)
            print(f'{prefix} {left} | {right}')
        print(f'{prefix} {sep}    bar: W={self.bar["W"]} B={self.bar["B"]}')
        for row in range(4, -1, -1):
            left = ''.join(cell(p, row) for p in BOT_LEFT)
            right = ''.join(cell(p, row) for p in BOT_RIGHT)
            print(f'{prefix} {left} | {right}')
        print(f'{prefix} {sep}')
        print(f'{prefix}{fmt_labels(BOT_LEFT, BOT_RIGHT)}')
        print(f'{prefix} borne off: W={self.borne_off["W"]} B={self.borne_off["B"]}')

    def get_state_for_agent(self, color, dice, in_game_points, game_num, max_usable, legal_subs):
        return {
            "board": list(self.board),
            "bar": dict(self.bar),
            "borne_off": dict(self.borne_off),
            "dice": list(dice),
            "your_color": color,
            "opponent_color": self.opponent(color),
            "turn_count": self.turn_count,
            "in_game_points": dict(in_game_points),
            "game_num": game_num,
            "legal_sub_moves": list(legal_subs),
            "max_dice_usable": max_usable,
        }
'''


# ============================================================
# Match runner code (subprocess: race-to-POINTS_TO_WIN_MATCH)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


def play_game(game_num, in_game_points, match_stats, names_for_color, agent_classes):
    """Play one game; mutate in_game_points and match_stats. Return (winner_label, pts_awarded)."""
    game = BackgammonGame()
    game.current_player = random.choice(['W', 'B'])

    print()
    print('=' * 60)
    print(f'Game {game_num}')
    a1_color = 'W' if names_for_color['W'] == 'Agent-1' else 'B'
    a2_color = 'W' if names_for_color['W'] == 'Agent-2' else 'B'
    print(f'Agent-1: {AGENT1_INFO} ({a1_color})')
    print(f'Agent-2: {AGENT2_INFO} ({a2_color})')
    print(f'First player: {game.current_player} ({names_for_color[game.current_player]})')
    print('-' * 60)

    agents = {}
    for color in ('W', 'B'):
        agent_name = names_for_color[color]
        try:
            agents[color] = agent_classes[agent_name](agent_name, color)
        except Exception as e:
            print(f'{agent_name} ({color}) init crash: {e}')
            match_stats[agent_name]['other_crash'] += 1
            opp_color = 'W' if color == 'B' else 'B'
            opp_name = names_for_color[opp_color]
            in_game_points[opp_name] += 2
            match_stats[opp_name]['wins'] += 1
            match_stats[agent_name]['losses'] += 1
            print('Final Position: N/A (initialization crash)')
            print('-' * 40)
            print(f'Final Result: {opp_name} wins by forfeit (Gammon-equivalent +2)')
            print('-' * 40)
            print('Points (in-game):')
            print(f'{opp_name}: 2')
            print(f'{agent_name}: 0')
            print('-' * 40)
            print('Match Score (in-game total):')
            print(f"Agent-1: {in_game_points['Agent-1']}")
            print(f"Agent-2: {in_game_points['Agent-2']}")
            print('=' * 60)
            return opp_name, 2

    result_winner = None
    result_kind = None
    game_over = False

    while not game_over:
        if game.turn_count >= MAX_TURNS_PER_GAME:
            result_kind = 'draw_turn_limit'
            game_over = True
            break

        color = game.current_player
        agent = agents[color]
        agent_name = names_for_color[color]
        game.turn_count += 1

        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        dice = [d1, d1, d1, d1] if d1 == d2 else [d1, d2]

        max_usable = game.max_dice_usable(color, dice)
        legal_subs = game.get_legal_sub_moves(color, dice)

        if max_usable == 0:
            print(f'Turn {game.turn_count}: {agent_name} ({color}) rolled {dice} -> no legal moves, skipping')
            game.current_player = game.opponent(color)
            done, w, k = game.is_game_over()
            if done:
                result_winner = w
                result_kind = k
                game_over = True
            continue

        state = game.get_state_for_agent(
            color, dice,
            {'W': in_game_points[names_for_color['W']],
             'B': in_game_points[names_for_color['B']]},
            game_num, max_usable, legal_subs,
        )
        sequence = None
        forfeited = False

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                sequence = agent.make_move(state, None)
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            print(f'Turn {game.turn_count}: {agent_name} ({color}) rolled {dice} -> TIMEOUT, forfeit')
            match_stats[agent_name]['timeout'] += 1
            forfeited = True
        except Exception as e:
            print(f'Turn {game.turn_count}: {agent_name} ({color}) rolled {dice} -> CRASH ({str(e)[:80]}), forfeit')
            match_stats[agent_name]['make_move_crash'] += 1
            forfeited = True

        if not forfeited:
            ok, msg, hits = game.validate_and_apply_turn(color, dice, sequence, max_usable=max_usable)
            if not ok:
                short_seq = repr(sequence)[:120]
                print(f'Turn {game.turn_count}: {agent_name} ({color}) rolled {dice} -> INVALID ({msg}), forfeit. Submitted: {short_seq}')
                match_stats[agent_name]['invalid'] += 1
                forfeited = True
            else:
                hit_str = f' [hit x{hits}]' if hits else ''
                print(f'Turn {game.turn_count}: {agent_name} ({color}) rolled {dice} -> {sequence}{hit_str}')
                match_stats[agent_name]['hits'] += hits
                match_stats[agent_name]['dice_used'] += len(sequence)

        done, w, k = game.is_game_over()
        if done:
            result_winner = w
            result_kind = k
            game_over = True
            break

        game.current_player = game.opponent(color)

    print()
    print('Final Position:')
    game.display_board()
    print(f'Total turns this game: {game.turn_count}')
    print('-' * 40)

    awarded_pts = 0
    if result_kind == 'draw_turn_limit':
        winner_label = 'DRAW'
        in_game_points['Agent-1'] += 0.5
        in_game_points['Agent-2'] += 0.5
        match_stats['Agent-1']['draws'] += 1
        match_stats['Agent-2']['draws'] += 1
        awarded_pts = 0.5
        result_desc = f'Draw by turn limit ({MAX_TURNS_PER_GAME} turns)'
    elif result_kind in ('single', 'gammon'):
        winner_label = names_for_color[result_winner]
        loser_label = 'Agent-2' if winner_label == 'Agent-1' else 'Agent-1'
        pts = 2 if result_kind == 'gammon' else 1
        in_game_points[winner_label] += pts
        match_stats[winner_label]['wins'] += 1
        match_stats[loser_label]['losses'] += 1
        awarded_pts = pts
        kind_label = 'Gammon' if result_kind == 'gammon' else 'Single'
        result_desc = f'{winner_label} ({result_winner}) wins by {kind_label} (+{pts})'
    else:
        winner_label = 'DRAW'
        in_game_points['Agent-1'] += 0.5
        in_game_points['Agent-2'] += 0.5
        match_stats['Agent-1']['draws'] += 1
        match_stats['Agent-2']['draws'] += 1
        awarded_pts = 0.5
        result_desc = 'Draw (unspecified)'

    print(f'Final Result: {result_desc}')
    print('-' * 40)
    print('Points (in-game):')
    if winner_label == 'DRAW':
        print('Agent-1: 0.5')
        print('Agent-2: 0.5')
    else:
        loser_label = 'Agent-2' if winner_label == 'Agent-1' else 'Agent-1'
        print(f'{winner_label}: {awarded_pts}')
        print(f'{loser_label}: 0')
    print('-' * 40)
    print('Match Score (in-game total):')
    print(f"Agent-1: {in_game_points['Agent-1']}")
    print(f"Agent-2: {in_game_points['Agent-2']}")
    print('=' * 60)
    sys.stdout.flush()
    return winner_label, awarded_pts


def main():
    match_stats = {
        'Agent-1': {'wins': 0, 'losses': 0, 'draws': 0, 'points': 0, 'score': 0.0,
                    'make_move_crash': 0, 'other_crash': 0, 'crash': 0,
                    'timeout': 0, 'invalid': 0, 'hits': 0, 'dice_used': 0},
        'Agent-2': {'wins': 0, 'losses': 0, 'draws': 0, 'points': 0, 'score': 0.0,
                    'make_move_crash': 0, 'other_crash': 0, 'crash': 0,
                    'timeout': 0, 'invalid': 0, 'hits': 0, 'dice_used': 0},
    }

    in_game_points = {'Agent-1': 0.0, 'Agent-2': 0.0}
    agent_classes = {'Agent-1': BackgammonAgent_1, 'Agent-2': BackgammonAgent_2}

    games_played = 0
    for game_num in range(1, MAX_GAMES_PER_MATCH + 1):
        if game_num % 2 == 1:
            names_for_color = {'W': 'Agent-1', 'B': 'Agent-2'}
        else:
            names_for_color = {'W': 'Agent-2', 'B': 'Agent-1'}

        play_game(game_num, in_game_points, match_stats, names_for_color, agent_classes)
        games_played += 1
        sys.stdout.flush()

        if (in_game_points['Agent-1'] >= POINTS_TO_WIN_MATCH
                or in_game_points['Agent-2'] >= POINTS_TO_WIN_MATCH):
            break

    a1_pts = in_game_points['Agent-1']
    a2_pts = in_game_points['Agent-2']

    if a1_pts >= POINTS_TO_WIN_MATCH and a2_pts >= POINTS_TO_WIN_MATCH:
        if a1_pts == a2_pts:
            league_a1, league_a2 = 1, 1
            score_a1 = score_a2 = 0.0
            outcome = 'DRAW (both reached 5 simultaneously)'
        elif a1_pts > a2_pts:
            league_a1, league_a2 = 3, 0
            score_a1 = a1_pts - a2_pts
            score_a2 = -score_a1
            outcome = 'Agent-1 wins'
        else:
            league_a1, league_a2 = 0, 3
            score_a2 = a2_pts - a1_pts
            score_a1 = -score_a2
            outcome = 'Agent-2 wins'
    elif a1_pts >= POINTS_TO_WIN_MATCH:
        league_a1, league_a2 = 3, 0
        score_a1 = a1_pts - a2_pts
        score_a2 = -score_a1
        outcome = 'Agent-1 wins'
    elif a2_pts >= POINTS_TO_WIN_MATCH:
        league_a1, league_a2 = 0, 3
        score_a2 = a2_pts - a1_pts
        score_a1 = -score_a2
        outcome = 'Agent-2 wins'
    else:
        if a1_pts > a2_pts:
            league_a1, league_a2 = 3, 0
            score_a1 = a1_pts - a2_pts
            score_a2 = -score_a1
            outcome = f'Agent-1 wins on tiebreak (game cap {MAX_GAMES_PER_MATCH})'
        elif a2_pts > a1_pts:
            league_a1, league_a2 = 0, 3
            score_a2 = a2_pts - a1_pts
            score_a1 = -score_a2
            outcome = f'Agent-2 wins on tiebreak (game cap {MAX_GAMES_PER_MATCH})'
        else:
            league_a1, league_a2 = 1, 1
            score_a1 = score_a2 = 0.0
            outcome = f'Match draw (game cap {MAX_GAMES_PER_MATCH})'

    match_stats['Agent-1']['points'] = league_a1
    match_stats['Agent-2']['points'] = league_a2
    match_stats['Agent-1']['score'] = score_a1
    match_stats['Agent-2']['score'] = score_a2

    for k in ('Agent-1', 'Agent-2'):
        match_stats[k]['crash'] = match_stats[k]['make_move_crash'] + match_stats[k]['other_crash']

    print('=' * 60)
    print(f'Agent-1: {AGENT1_INFO}')
    print(f'Agent-2: {AGENT2_INFO}')
    print(f'Match outcome: {outcome}')
    print(f'In-game total: Agent-1={a1_pts}, Agent-2={a2_pts}')
    print(f'Games played: {games_played}')
    print(f'RESULT:Agent-1={league_a1},Agent-2={league_a2}')
    print(f'SCORE:Agent-1={score_a1},Agent-2={score_a2}')
    print(f"WINS:Agent-1={match_stats['Agent-1']['wins']},Agent-2={match_stats['Agent-2']['wins']}")
    print(f"DRAWS:{match_stats['Agent-1']['draws']}")

    print('--- MATCH STATISTICS ---')
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
    print(f"Agent-1 Hits: {match_stats['Agent-1']['hits']}")
    print(f"Agent-2 Hits: {match_stats['Agent-2']['hits']}")
    print(f"Agent-1 In-Game Points: {a1_pts}")
    print(f"Agent-2 In-Game Points: {a2_pts}")
    print(f"Games Played: {games_played}")
    print(f"STATS:Agent-1={match_stats['Agent-1']}")
    print(f"STATS:Agent-2={match_stats['Agent-2']}")
    print(f"GAMES_PLAYED:{games_played}")


if __name__ == "__main__":
    main()
'''


# ============================================================
# Human play mode code (interactive: humanvsbot, humanvshuman, humanvsagent)
# ============================================================
HUMAN_PLAY_CODE = r'''
import datetime
import os


class HumanAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        dice = state['dice']
        max_usable = state['max_dice_usable']
        legal = state['legal_sub_moves']

        print()
        print(f"{self.name} ({self.color}) - dice: {dice}, must use {max_usable} dice")
        if state['bar'][self.color] > 0:
            print(f"You have {state['bar'][self.color]} checker(s) on the bar.")
        if max_usable == 0:
            print('No legal moves. Press Enter to skip turn.')
            input('> ')
            return []
        print('Legal single sub-moves from current state:')
        for sub in legal:
            print(f'  {sub}')
        print('Enter your sub-moves (space-separated): from1,to1 from2,to2 ...')
        print("Use 'bar' for from when entering from bar; 'off' for to when bearing off.")

        while True:
            line = input('> ').strip()
            if not line:
                return []
            try:
                pairs = line.split()
                seq = []
                for p in pairs:
                    parts = p.split(',')
                    if len(parts) != 2:
                        raise ValueError(f"Bad sub-move format: {p}")
                    f, t = parts[0].strip(), parts[1].strip()
                    f_v = 'bar' if f == 'bar' else int(f)
                    t_v = 'off' if t == 'off' else int(t)
                    seq.append((f_v, t_v))
                return seq
            except (ValueError, IndexError) as e:
                print(f'Bad input: {e}. Try again.')


class RandomAgent:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        # Reconstruct a temporary engine from state to enumerate sequences.
        g = BackgammonGame()
        g.board = list(state['board'])
        g.bar = dict(state['bar'])
        g.borne_off = dict(state['borne_off'])

        dice = list(state['dice'])
        color = state['your_color']
        seq = []
        while True:
            legal = g.get_legal_sub_moves(color, dice)
            if not legal:
                break
            sub = random.choice(legal)
            die = g._find_die_for_sub(color, sub, dice)
            if die is None:
                break
            g._apply_sub_move(color, sub)
            seq.append(sub)
            dice.remove(die)
            if not dice:
                break
        return seq


MAX_TURNS_PER_GAME = 300
POINTS_TO_WIN_MATCH = 5
MAX_GAMES_PER_MATCH = 30

MODE_TITLES = {
    'humanvsbot': 'Human vs Random Bot',
    'humanvshuman': 'Human vs Human',
    'humanvsagent': 'Human vs Stored Agent',
}


def play_human_match():
    mode_title = MODE_TITLES.get(GAME_MODE, GAME_MODE)
    print('=' * 60)
    print(f'BACKGAMMON - {mode_title}')
    print(f'Race to {POINTS_TO_WIN_MATCH} in-game points')
    print('=' * 60)

    if GAME_MODE == 'humanvsbot':
        if random.random() < 0.5:
            agents = {'W': HumanAgent('Human', 'W'), 'B': RandomAgent('Bot', 'B')}
            print('You are W.')
        else:
            agents = {'W': RandomAgent('Bot', 'W'), 'B': HumanAgent('Human', 'B')}
            print('You are B.')
    elif GAME_MODE == 'humanvshuman':
        agents = {'W': HumanAgent('Player 1', 'W'), 'B': HumanAgent('Player 2', 'B')}
    elif GAME_MODE == 'humanvsagent':
        if random.random() < 0.5:
            agents = {'W': HumanAgent('Human', 'W'), 'B': BackgammonAgent_1('Agent', 'B')}
            print('You are W.')
        else:
            agents = {'W': BackgammonAgent_1('Agent', 'W'), 'B': HumanAgent('Human', 'B')}
            print('You are B.')

    in_game = {'W': 0.0, 'B': 0.0}

    for game_num in range(1, MAX_GAMES_PER_MATCH + 1):
        print()
        print('#' * 60)
        print(f'GAME {game_num}  (Match score W={in_game["W"]} B={in_game["B"]})')
        print('#' * 60)

        game = BackgammonGame()
        game.current_player = random.choice(['W', 'B'])
        print(f'First player: {game.current_player}')
        game.display_board(prefix='')

        while True:
            if game.turn_count >= MAX_TURNS_PER_GAME:
                print('Turn limit reached, draw.')
                in_game['W'] += 0.5
                in_game['B'] += 0.5
                break

            color = game.current_player
            game.turn_count += 1
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            dice = [d1, d1, d1, d1] if d1 == d2 else [d1, d2]
            print()
            print(f'--- Turn {game.turn_count}: {color} rolled {dice} ---')

            max_usable = game.max_dice_usable(color, dice)
            legal_subs = game.get_legal_sub_moves(color, dice)

            if max_usable == 0:
                print(f'{color} has no legal moves, skipping.')
            else:
                state = game.get_state_for_agent(
                    color, dice, in_game, game_num, max_usable, legal_subs,
                )
                seq = agents[color].make_move(state, None)
                ok, msg, hits = game.validate_and_apply_turn(color, dice, seq, max_usable=max_usable)
                if not ok:
                    print(f'{color}: invalid ({msg}). Forfeit turn.')
                else:
                    print(f'{color} played: {seq}')
                    if hits:
                        print(f'{color} hit {hits} blot(s).')

            game.display_board(prefix='')

            done, w, k = game.is_game_over()
            if done:
                pts = 2 if k == 'gammon' else 1
                in_game[w] += pts
                print(f'\n{w} wins by {k}! (+{pts} in-game point{"s" if pts > 1 else ""})')
                break

            game.current_player = game.opponent(color)

        if in_game['W'] >= POINTS_TO_WIN_MATCH or in_game['B'] >= POINTS_TO_WIN_MATCH:
            break

    print()
    print('=' * 60)
    print('MATCH OVER')
    print(f"Final score: W={in_game['W']}, B={in_game['B']}")
    if in_game['W'] > in_game['B']:
        print('WHITE wins the match.')
    elif in_game['B'] > in_game['W']:
        print('BLACK wins the match.')
    else:
        print('Match draw.')

    try:
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backgammon_{GAME_MODE}_{ts}.txt'
        log_dir = '.'
        if os.path.exists('../results/backgammon'):
            log_dir = '../results/backgammon'
        elif os.path.exists('results/backgammon'):
            log_dir = 'results/backgammon'
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'w') as f:
            f.write(f'Backgammon Game - {mode_title}\n')
            f.write(f'Date: {datetime.datetime.now()}\n')
            f.write(f"Final score: W={in_game['W']} B={in_game['B']}\n")
        print(f'\nGame report saved to: {filepath}')
    except Exception as e:
        print(f'Could not save game report: {e}')


if __name__ == '__main__':
    play_human_match()
'''


def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / f"{GAME_NAME}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


def find_model_folder(pattern: str) -> str | None:
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

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


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs


def build_game_code(
    agent1_code: str,
    agent2_code: str,
    extra_imports: str,
    move_timeout: float,
    max_turns: int,
    points_to_win: int,
    max_games: int,
    agent1_info: str,
    agent2_info: str,
) -> str:
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "import time\n"
        "import collections\n"
        "import math\n"
        "import itertools\n"
        "import copy\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"MAX_TURNS_PER_GAME = {max_turns}\n"
        f"POINTS_TO_WIN_MATCH = {points_to_win}\n"
        f"MAX_GAMES_PER_MATCH = {max_games}\n"
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
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = MATCH_TIME_LIMIT
) -> dict:
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"backgammon_match_{match_id}_{temp_id}.py"
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
            r"RESULT:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", result.stdout
        )

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            wins_match = re.search(r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout)
            draws_match = re.search(r"DRAWS:(\d+)", result.stdout)
            score_match = re.search(
                r"SCORE:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", result.stdout
            )
            games_match = re.search(r"GAMES_PLAYED:(\d+)", result.stdout)

            agent1_wins = int(wins_match.group(1)) if wins_match else 0
            agent2_wins = int(wins_match.group(2)) if wins_match else 0
            draws = int(draws_match.group(1)) if draws_match else 0
            agent1_points = int(float(match.group(1)))
            agent2_points = int(float(match.group(2)))
            agent1_score = float(score_match.group(1)) if score_match else 0.0
            agent2_score = float(score_match.group(2)) if score_match else 0.0
            games_played = int(games_match.group(1)) if games_match else (agent1_wins + agent2_wins + draws)

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
                "games_played": games_played,
                "error": None,
                "stats_block": stats_block,
                "log": result.stdout,
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
    parser = argparse.ArgumentParser(description="Run Backgammon matches")
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
    parser.add_argument(
        "--update-scoreboard", action="store_true",
        help="Write results to scoreboard (default: off; enabled by matchmaker)",
    )
    parser.add_argument(
        "--parallel", type=int, default=4,
        help="Number of matches to run in parallel",
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
                folder, GAME_NAME, runs[0], 1, "BackgammonAgent"
            )
            if not agent_code:
                print(f"ERROR: Failed to load agent from {folder}")
                sys.exit(1)
            game_code = build_human_game_code("humanvsagent", agent_code, agent_imports)
        elif args.agent:
            print("ERROR: --agent is not used with --humanvsbot or --humanvshuman.")
            sys.exit(1)
        else:
            game_code = build_human_game_code(human_mode)

        temp_file = os.path.join(
            tempfile.gettempdir(),
            f"backgammon_{human_mode}_{uuid.uuid4().hex[:8]}.py",
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

    runs_explicitly_specified = bool(runs1 or runs2)

    if not runs1:
        runs1 = get_available_runs(folder1, GAME_NAME)
    if not runs2:
        runs2 = get_available_runs(folder2, GAME_NAME)

    num_matches = min(len(runs1), len(runs2))
    if not runs_explicitly_specified:
        runs1 = runs1[:num_matches] * args.parallel
        runs2 = runs2[:num_matches] * args.parallel
    else:
        runs1 = runs1[:num_matches]
        runs2 = runs2[:num_matches]
    num_matches = len(runs1)

    print("\n" + "=" * 60)
    print("BACKGAMMON MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print(f"Race target: {POINTS_TO_WIN_MATCH} in-game points (max {MAX_GAMES_PER_MATCH} games)")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    match_tasks = []
    semaphore = asyncio.Semaphore(args.parallel)

    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]

        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1, "BackgammonAgent")
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2, "BackgammonAgent")

        if not code1 or not code2:
            print(f"  FAILED to load match {i + 1}")
            continue

        extra_imports = consolidate_imports(imp1, imp2, COMMON_HEADER_IMPORTS)

        agent1_info = f"{folder1}:{run1}"
        agent2_info = f"{folder2}:{run2}"

        game_code = build_game_code(
            code1, code2, extra_imports,
            MOVE_TIME_LIMIT, MAX_TURNS_PER_GAME,
            POINTS_TO_WIN_MATCH, MAX_GAMES_PER_MATCH,
            agent1_info, agent2_info,
        )

        async def sem_task(gc, mid, rids):
            async with semaphore:
                return await run_match_async(gc, mid, rids)

        match_tasks.append(sem_task(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    match_word = "match" if len(match_tasks) == 1 else "matches"
    parallel_info = f" (up to {args.parallel} in parallel)" if len(match_tasks) > 1 else ""
    print(f"\nRunning {len(match_tasks)} {match_word}{parallel_info}...")
    results = await asyncio.gather(*match_tasks)

    total1, total2 = 0.0, 0.0
    total_pts1, total_pts2 = 0, 0

    for result in sorted(results, key=lambda x: x["match_id"]):
        match_id = result["match_id"]
        run1 = runs1[match_id - 1]
        run2 = runs2[match_id - 1]
        log_f = RESULTS_DIR / f"{ts}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt"
        p1, p2 = 0, 0

        if result["success"]:
            s1, s2 = result["agent1_score"], result["agent2_score"]
            p1 = result.get("agent1_points", 0)
            p2 = result.get("agent2_points", 0)
            total1 += s1
            total2 += s2
            total_pts1 += p1
            total_pts2 += p2

            status = "Result:\n"
            status += f"{folder1}:{run1} : Pts: {p1} - Score: {s1:.1f}\n"
            status += f"{folder2}:{run2} : Pts: {p2} - Score: {s2:.1f}\n"

            game_log = result.get("log", "")
            if game_log:
                status += f"\n{game_log}\n"
        else:
            status = f"FAILED: {result.get('error', 'Unknown')}"

        print(f"Match {match_id} Completed. Pts {p1}-{p2}")
        if result["success"]:
            print(f"MINI:{folder1}:{run1}={p1},{s1}|{folder2}:{run2}={p2},{s2}")

        with open(log_f, "w") as f:
            f.write("Match Contenders:\n")
            f.write(f"{folder1}:{run1}\n")
            f.write(f"{folder2}:{run2}\n\n")
            f.write(f"{status}\n")
            f.write("-" * 60 + "\n")

        if result["success"] and args.update_scoreboard:
            games_played = result.get("games_played", 0)
            agent1_key = f"{folder1}:{run1}"
            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=games_played,
                wins=result.get("agent1_wins", 0),
                losses=result.get("agent2_wins", 0),
                draws=result.get("draws", 0),
                score=result["agent1_score"],
                points=result.get("agent1_points", 0),
            )
            agent2_key = f"{folder2}:{run2}"
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=games_played,
                wins=result.get("agent2_wins", 0),
                losses=result.get("agent1_wins", 0),
                draws=result.get("draws", 0),
                score=result["agent2_score"],
                points=result.get("agent2_points", 0),
            )

    runs1_str = ",".join(str(r) for r in runs1)
    runs2_str = ",".join(str(r) for r in runs2)
    print("\nFINAL RESULTS:")
    print(f"  {folder1}:{runs1_str}: Pts {total_pts1}, Score {total1:.1f}")
    print(f"  {folder2}:{runs2_str}: Pts {total_pts2}, Score {total2:.1f}")
    print(f"\nLogs saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    asyncio.run(main_async())
