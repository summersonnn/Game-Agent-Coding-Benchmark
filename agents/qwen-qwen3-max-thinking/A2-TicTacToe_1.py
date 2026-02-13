"""
Agent Code: A2-TicTacToe
Model: qwen/qwen3-max-thinking
Run: 1
Generated: 2026-02-13 14:10:12
"""



class TicTacToeAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.win_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]

    def make_move(self, board):
        available = [i for i, cell in enumerate(board) if cell == ' ']
        if len(available) == 1:
            return available[0]

        def check_winner_state(state):
            for a, b, c in self.win_lines:
                if state[a] != ' ' and state[a] == state[b] == state[c]:
                    return state[a]
            return 'DRAW' if ' ' not in state else None

        win_moves = []
        for move in available:
            new_state = board.copy()
            new_state[move] = self.symbol
            if check_winner_state(new_state) == self.symbol:
                win_moves.append(move)
        if win_moves:
            pref_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
            for p in pref_order:
                if p in win_moves:
                    return p

        block_moves = []
        for move in available:
            new_state = board.copy()
            new_state[move] = self.opponent
            if check_winner_state(new_state) == self.opponent:
                block_moves.append(move)
        if len(block_moves) == 1:
            return block_moves[0]

        cache = {}

        def minimax(state_tuple):
            if state_tuple in cache:
                return cache[state_tuple]
            
            winner = check_winner_state(state_tuple)
            if winner is not None:
                empty_rem = state_tuple.count(' ')
                if winner == self.symbol:
                    score = 100 + max(empty_rem, 3)
                elif winner == self.opponent:
                    score = -100 - max(empty_rem, 3)
                else:
                    score = 0
                cache[state_tuple] = score
                return score

            cnt_x = state_tuple.count('X')
            cnt_o = state_tuple.count('O')
            current_player = 'X' if cnt_x == cnt_o else 'O'
            is_self_turn = (current_player == self.symbol)

            if is_self_turn:
                best_val = -10**9
                for i in range(9):
                    if state_tuple[i] == ' ':
                        lst = list(state_tuple)
                        lst[i] = self.symbol
                        new_tuple = tuple(lst)
                        val = minimax(new_tuple)
                        if val > best_val:
                            best_val = val
                cache[state_tuple] = best_val
                return best_val
            else:
                best_val = 10**9
                for i in range(9):
                    if state_tuple[i] == ' ':
                        lst = list(state_tuple)
                        lst[i] = self.opponent
                        new_tuple = tuple(lst)
                        val = minimax(new_tuple)
                        if val < best_val:
                            best_val = val
                cache[state_tuple] = best_val
                return best_val

        best_score = -10**9
        best_moves = []
        for move in available:
            new_state = board.copy()
            new_state[move] = self.symbol
            score = minimax(tuple(new_state))
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        pref_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        for p in pref_order:
            if p in best_moves:
                return p
        return best_moves[0] if best_moves else available[0]
