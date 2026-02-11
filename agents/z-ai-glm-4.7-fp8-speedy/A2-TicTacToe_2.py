"""
Agent Code: A2-TicTacToe
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-11 20:47:17
"""



class TicTacToeAgent:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        
        # Predefined winning combinations (indices)
        self.win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]

    def make_move(self, board: list[str]) -> int:
        """
        Determines the best move using the Minimax algorithm.
        """
        # Get all legal moves
        available_moves = [i for i, spot in enumerate(board) if spot == ' ']
        
        # If no moves available (should not happen if game is running), return 0
        if not available_moves:
            return 0

        # Optimization: If the board is empty, take the center.
        # This is the statistically strongest opening move.
        if len(available_moves) == 9:
            return 4
        
        # Optimization: If only one move is available, take it immediately.
        if len(available_moves) == 1:
            return available_moves[0]

        best_score = -float('inf')
        best_move = available_moves[0]

        # Iterate through all available moves to find the one with the highest minimax score
        for move in available_moves:
            # Simulate the move
            board[move] = self.symbol
            
            # Call minimax to evaluate the board state resulting from this move
            # Depth is 0 because we are evaluating the immediate result of this move
            # is_maximizing is False because the next turn belongs to the opponent
            score = self.minimax(board, 0, False)
            
            # Undo the move to restore board state for the next iteration
            board[move] = ' '

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, board: list[str], depth: int, is_maximizing: bool) -> int:
        """
        Recursive Minimax algorithm to evaluate board states.
        Returns a score representing the favorability of the board.
        """
        # Check for terminal states (Win, Loss, Draw)
        winner = self.check_winner(board)
        
        if winner == self.symbol:
            # AI wins: Return positive score.
            # Subtract depth to prioritize winning faster (fewer moves).
            return 10 - depth
        elif winner == self.opponent_symbol:
            # Opponent wins: Return negative score.
            # Add depth to prioritize losing slower (more moves), delaying the inevitable.
            return depth - 10
        elif ' ' not in board:
            # Draw: Return neutral score
            return 0

        if is_maximizing:
            # AI's turn: Maximize score
            best_score = -float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.symbol
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            # Opponent's turn: Minimize score
            best_score = float('inf')
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.opponent_symbol
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def check_winner(self, board: list[str]) -> str | None:
        """
        Checks the board for a winner.
        Returns 'X', 'O', or None.
        """
        for combo in self.win_combinations:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]
        return None
