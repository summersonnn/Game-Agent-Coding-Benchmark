"""
Agent Code: A2-TicTacToe
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-13 14:53:21
"""



class TicTacToeAgent:
    """
    Smart Tic Tac Toe agent for 5x5, 3-in-a-row rules.
    Strategy (in priority):
      1) Win immediately if possible.
      2) Block opponent immediate win(s).
      3) Create a fork (move that yields >=2 immediate wins next turn).
      4) Block opponent forks (try direct block, then force-response threats, otherwise minimize forks).
      5) Take center (index 12) if available.
      6) Heuristic: maximize own future threats/open lines and minimize opponent's.
    """
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # 'X' or 'O'
        self.EMPTY = ' '
        # Precompute winning triples (same as game logic)
        combos = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                combos.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                combos.append((start, start + 5, start + 10))
        # Diagonals down-right
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                combos.append((start, start + 6, start + 12))
        # Diagonals down-left
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                combos.append((start, start + 4, start + 8))
        self.combos = combos
        # Map cell -> combos that include it for quick access
        self.cell_to_combos = {i: [] for i in range(25)}
        for combo in self.combos:
            for idx in combo:
                self.cell_to_combos[idx].append(combo)

    # Helper: immediate winning moves for player on given board
    def _immediate_winning_moves(self, board, player):
        moves = []
        for combo in self.combos:
            a, b, c = combo
            marks = (board[a], board[b], board[c])
            if marks.count(player) == 2 and marks.count(self.EMPTY) == 1:
                for idx in combo:
                    if board[idx] == self.EMPTY:
                        moves.append(idx)
                        break
        return moves

    # Helper: fork moves for player (moves that create >=2 immediate wins next turn)
    def _fork_moves(self, board, player):
        forks = []
        avail = [i for i, v in enumerate(board) if v == self.EMPTY]
        for m in avail:
            board2 = board[:]
            board2[m] = player
            wins_next = set(self._immediate_winning_moves(board2, player))
            if len(wins_next) >= 2:
                forks.append(m)
        return forks

    def make_move(self, board):
        my = self.symbol
        opp = 'O' if my == 'X' else 'X'
        available = [i for i, v in enumerate(board) if v == self.EMPTY]
        if not available:
            return 0  # fallback

        # 1) Immediate win
        my_wins = self._immediate_winning_moves(board, my)
        if my_wins:
            return random.choice(list(set(my_wins)))

        # 2) Block opponent immediate wins
        opp_wins = self._immediate_winning_moves(board, opp)
        if opp_wins:
            # If there's a single unique block, play it
            uniq = list(set(opp_wins))
            if len(uniq) == 1:
                return uniq[0]
            # Otherwise pick the block that appears most often (blocks the most threats)
            counts = {}
            for pos in opp_wins:
                counts[pos] = counts.get(pos, 0) + 1
            max_count = max(counts.values())
            best = [pos for pos, cnt in counts.items() if cnt == max_count and board[pos] == self.EMPTY]
            if best:
                return random.choice(best)

        # 3) Create fork if possible
        my_forks = self._fork_moves(board, my)
        if my_forks:
            return random.choice(my_forks)

        # 4) Block opponent forks
        opp_forks = self._fork_moves(board, opp)
        if opp_forks:
            uniq_forks = list(set(opp_forks))
            # If only one fork position, occupy it if possible
            if len(uniq_forks) == 1 and board[uniq_forks[0]] == self.EMPTY:
                return uniq_forks[0]
            # Try to create a immediate threat forcing opponent to respond
            threat_moves = []
            for m in available:
                board2 = board[:]
                board2[m] = my
                if len(set(self._immediate_winning_moves(board2, my))) >= 1:
                    threat_moves.append(m)
            if threat_moves:
                return random.choice(threat_moves)
            # Otherwise choose a move that reduces opponent fork count the most
            best_m = None
            best_blocked = -1
            original_forks = set(uniq_forks)
            for m in available:
                board2 = board[:]
                board2[m] = my
                remaining = set(self._fork_moves(board2, opp))
                blocked = len(original_forks) - len(remaining)
                if blocked > best_blocked:
                    best_blocked = blocked
                    best_m = m
            if best_m is not None:
                return best_m

        # 5) Take center if available
        center = 12
        if center in available:
            return center

        # 6) Heuristic: prefer moves that create threats and maximize open lines for us while minimizing opponent's
        best_score = -10**9
        best_moves = []
        for m in available:
            board2 = board[:]
            board2[m] = my
            my_two_after = len(set(self._immediate_winning_moves(board2, my)))
            # Count open lines containing m for both players (after our move)
            my_open = 0
            opp_open = 0
            for combo in self.cell_to_combos[m]:
                if not any(board2[i] == opp for i in combo):
                    my_open += 1
                if not any(board2[i] == my for i in combo):
                    opp_open += 1
            # Score weights chosen to prioritize immediate threats and open lines
            score = my_two_after * 200 + my_open * 10 - opp_open * 8
            # small randomness to break ties and avoid deterministic play
            score += random.uniform(-1, 1)
            if score > best_score:
                best_score = score
                best_moves = [m]
            elif abs(score - best_score) < 1e-6:
                best_moves.append(m)

        if best_moves:
            return random.choice(best_moves)

        # Fallback (shouldn't reach often)
        return random.choice(available)
