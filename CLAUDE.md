# Competitive LLM Agents

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # Configuration: models.txt
game_scripts/     # Match runners (*_match.py) and the matchmaker
games/            # Game prompts/rules (A1-Battleship, A2-LieOnce, ...)
results/          # Match logs and outcomes
scoreboard/       # Per-game leaderboards (A1-scoreboard.txt, ...)
utils/            # Core logic - API client, agent generation, scoreboard
```

## Entry Points

**Agent Generation:**
```bash
uv run utils/populate_agents.py --all                           # All models, all games
uv run utils/populate_agents.py --model Terra Opus             # Specific models
uv run utils/populate_agents.py --game A1,A5 --runs 3           # Specific games
```

**Running Individual Matches:**
```bash
uv run game_scripts/A1-battleship_match.py --agent Terra:1 Opus:1
uv run game_scripts/A2-lie_once_match.py --agent Terra:1 Opus:1
uv run game_scripts/A4-backgammon_match.py --agent Terra:1 Opus:1
uv run game_scripts/A5-connect4_match.py --agent Terra:1 Opus:1
uv run game_scripts/A6-word_matrix_match.py --agent Terra:1 Opus:1
uv run game_scripts/A7-mancala_match.py --agent Terra:1 Opus:1
uv run game_scripts/A8-surround_morris_match.py --agent Terra:1 Opus:1
```

> Individual match runners also accept `--update-scoreboard` to persist results to the scoreboard file. Omit it for ad-hoc test matches; the matchmaker appends it automatically for tournament runs.

**Running Tournaments (Matchmaker):**
```bash
uv run game_scripts/matchmaker.py --game A8 --same_opponent_match 4
uv run game_scripts/matchmaker.py --game A8 --dry-run
uv run game_scripts/matchmaker.py --game A8 --new-model GPT-6.2-Astra-Extrahigh --health
uv run game_scripts/matchmaker.py --game A8 --mini --agent GPT-6.1-Terra-Extrahigh:1 GPT-6.1-Terra-Extrahigh:2 Gemini-Hydrogen-Extrahigh:1 Gemini-Hydrogen-Extrahigh:2 Opus-5.5-Max:1 Opus-5.5-Max:2 --same_opponent_match 4
uv run game_scripts/matchmaker.py --game A8 --mini --agent Opus-5.5-Max   # all runs of one model
```

> Mini leagues (`--mini`) do not pass `--update-scoreboard`, so they leave `scoreboard/` unchanged; they print a standings table at the end instead. See [Matchmaker](#matchmaker-tournament-scheduler).

**Agent Enhancement:**
```bash
uv run utils/try_enhancing_agents.py --model Terra --game A5        # Single model, single game
uv run utils/try_enhancing_agents.py --model Terra Opus --game A1,A5  # Multiple
uv run utils/try_enhancing_agents.py --model all --game all           # All 2-player combos
```

## Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client |
| `utils/game_config.py` | Independent per-game match counts and Wizard phase settings |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `utils/try_enhancing_agents.py` | Agent quality improvement via same-model benchmarking |
| `game_scripts/*_match.py` | Game-specific match orchestrators |
| `game_scripts/matchmaker.py` | Round-robin tournament scheduler and mini league runner |
| `utils/logging_config.py` | Centralized logging setup |
| `utils/scoreboard.py` | Atomic, file-locked scoreboard updates |
| `global_game_rules.md` | Canonical specification for all match runners: scoring system, output format, error taxonomy, log format, agent coding standards |

## Configuration

**.env Variables:**
- `MODEL_API_BASE_URL` - OpenRouter endpoint
- `MODEL_API_KEY` - API key
- `MODEL_MAX_TOKENS` - Base token limit (8192)
- `MODEL_TEMPERATURE` - Sampling temperature (0.7)
- `MODEL_API_TIMEOUT` - Per-request timeout for OpenRouter API calls in seconds (600)
- `MAX_WORKERS` - Concurrency limit for agent generation (default 16)
- `NUM_RUNS` - Default agent runs per model/game (default 2)
- `A1_GAMES_PER_MATCH` (default 20), `A2_GAMES_PER_MATCH` (default 50), `A3_GAMES_PER_MATCH` (default 24) - Independent match counts
- `A3_QUALIFIER_GAMES_PER_MATCH` (default 402), `A3_MAIN_EVENT_GAMES_PER_MATCH` (default 6) - Independent Wizard tournament phase counts; all Wizard defaults are multiples of six for equal seat coverage
- `A4_MAX_GAMES_PER_MATCH` - Backgammon game cap (default 30; race to five points)
- `A5_GAMES_PER_MATCH` (default 10), `A6_GAMES_PER_MATCH` (default 10), `A7_GAMES_PER_MATCH` (default 12), `A8_GAMES_PER_MATCH` (default 20) - Independent match counts
- `utils/game_config.py` defines each game's own default; invalid or non-positive counts fall back to that default

**config/models.txt:** Lists the 12 current benchmark model names, exactly matching `agents/` folders. All non-empty lines are active. Generation sends names unchanged to the configured API endpoint; saved agents contain no provider-ID mapping. Verify that the endpoint accepts these names before generation. Matchmaking discovers saved files independently of this list.

For a fresh Wizard roster, generate two runs per model. Population appends runs
to existing agents, while the Wizard tournament requires exactly two.

## Games Overview

| ID | Game | Players | Status |
|----|------|---------|--------|
| A1 | Battleship | 2 | Playable |
| A2 | LieOnce | 2 | Playable |
| A3 | Wizard | 6 | Playable |
| A4 | Backgammon | 2 | Playable |
| A5 | Connect4RandomStart | 2 | Playable |
| A6 | WordMatrixGame | 2 | Playable |
| A7 | Mancala | 2 | Playable |
| A8 | SurroundMorris | 2 | Playable |

---

## Game Details

### A8: Surround Morris

**Type:** 2-player competitive board game
**Match File:** `game_scripts/A8-surround_morris_match.py`
**Game Prompt:** `games/A8-SurroundMorris.txt`
**Scoreboard:** `scoreboard/A8-scoreboard.txt`

#### Overview

Nine Men's Morris variant where capture uses spatial surrounding instead of mill formation. Players place and move pieces on a 24-spot board, attempting to surround opponent pieces using the "overwhelm" capture rule.

#### Board Structure

24 spots arranged in three concentric squares with connecting lines:
```
 0----------1----------2
 |           |           |
 |   3-------4-------5   |
 |   |       |       |   |
 |   |   6---7---8   |   |
 |   |   |       |   |   |
 9---10--11      12--13--14
 |   |   |       |   |   |
 |   |   15--16--17  |   |
 |   |       |       |   |
 |   18------19------20  |
 |           |           |
 21----------22----------23
```

**Adjacency:** Each spot connects only to directly adjacent spots (horizontal/vertical lines). See `ADJACENCY` dict in code for complete mapping.

#### Game Phases

**1. Placement Phase**
- Each player starts with 7 pieces in hand (reduced from traditional 9)
- Players alternate placing one piece per turn on any empty spot
- Black (B) moves first
- Phase ends when both players have placed all 7 pieces

**2. Movement Phase**
- Players alternate moving one piece to an adjacent empty spot
- No flying (must move along board lines)
- Continues until game end condition met

#### Capture Mechanics: The "Overwhelm" Rule

A piece is captured when it satisfies BOTH conditions:
1. **Zero empty neighbors** (completely surrounded)
2. **More opponent neighbors than friendly neighbors**

**Capture Timing:** After every move (placement or movement), a two-pass capture sweep occurs:
1. **Self-harm priority:** Remove mover's captured pieces first
2. **Enemy capture:** Re-check opponent pieces (may gain empty neighbors from step 1)

**Suicide Moves:** Placing/moving into a captured position immediately removes your own piece.

#### Win/Draw Conditions

**Win by Elimination:**
- Opponent has 0 pieces on board AND 0 pieces in hand
- Self-harm priority: mover checked first for elimination

**Win by Mate:**
- Opponent has no legal moves at start of their turn
- Scored as +7/-7 (winner/loser)

**Draw by Repetition:**
- Same board state + current player occurs 3 times
- Checked before move execution

**Draw by Turn Limit:**
- 200 movement turns reached (configurable: `A8_MAX_TURNS_PER_GAME`)
- Checked after move execution

**Draw by Time Limit:**
- The game has run for `GAME_TIME_LIMIT` (150s, agent setup included); see [Game Time Limits](#game-time-limits)
- Checked before every move (placement and movement); scored like any other draw
- Exists so every match finishes with a result and every agent plays the same number of matches. Agents are not told about it in the prompt

#### Scoring System (Football League Style)

**Points (Primary Ranking Metric):**
- Win = 3 points
- Draw = 1 point
- Loss = 0 points

**Score (Tiebreaker, Goal Difference):**
- **Normal Win:** Winner gets +pieces_on_board, loser gets -pieces_on_board
- **Mate Win:** Winner gets +7, loser gets -7
- **Draw:** Each player gets 0

**Example:** Agent wins by elimination with five pieces remaining → +3 points, +5 score. Loser → 0 points, -5 score.

#### Leaderboard

**File:** `scoreboard/A8-scoreboard.txt`

**Format:**
```
Agent | Games | Wins | Losses | Draws | Points | Score
```

**Sorting:** Primary by Points (descending), tiebreaker by Score (descending)

**Update Logic:** Atomic file-locking via `utils/scoreboard.py:update_scoreboard()` using `fcntl.flock`. A sibling `.lock` file (e.g., `A8-scoreboard.lock`) is created during writes and persists if a process crashes — safe to delete manually if no matches are running. Backward-compatible with legacy 6-column format; missing Points column defaults to 0.

#### Code Architecture

**Embedded Subprocess Model:**

The match runner uses a multi-layer architecture:

1. **Outer Layer (`main_async`):**
   - CLI argument parsing
   - Agent discovery and loading
   - Match orchestration (parallel via `asyncio.gather`)
   - Result aggregation and logging
   - Scoreboard updates

2. **Middle Layer (`run_match`):**
   - Generates temporary Python file with embedded code
   - Spawns the subprocess with a hard kill at `MATCH_TIME_LIMIT` + 60s (`MATCH_KILL_GRACE`), where `MATCH_TIME_LIMIT` = `GAME_TIME_LIMIT` × games; normally the subprocess finishes by itself thanks to time-limit draws
   - Parses stdout for structured results (`RESULT:`, `SCORE:`, `WINS:`, `DRAWS:`)
   - Returns result dict

3. **Inner Layer (Embedded `MATCH_RUNNER_CODE`):**
   - Executed inside subprocess
   - Runs `NUM_GAMES_PER_MATCH` games (configured directly via `A8_GAMES_PER_MATCH`, default 20)
   - Tracks match statistics (wins, points, scores, errors)
   - Emits structured output lines for outer parsing

**Code Modules:**

| Module | Purpose |
|--------|---------|
| `GAME_ENGINE_CODE` | `SurroundMorrisGame` class, adjacency map, board logic |
| `MATCH_RUNNER_CODE` | `play_game()`, `main()`, timeout handling, stats tracking |
| `HUMAN_PLAY_CODE` | Human vs Bot/Human/Agent interactive mode |

These are embedded raw-string blocks in `game_scripts/A8-surround_morris_match.py`; search for the names rather than relying on line numbers.

**Agent Interface:**

Generated agents must implement:
```python
class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    def make_move(self, state: dict, feedback: dict | None):
        # Placement phase: return int (spot 0-23)
        # Movement phase: return tuple (from_spot, to_spot)
```

**State Dictionary:**
```python
{
    "board": list[str],           # 24 elements: '', 'B', or 'W'
    "phase": str,                 # 'placement' or 'movement'
    "your_color": str,            # 'B' or 'W'
    "opponent_color": str,        # 'W' or 'B'
    "pieces_in_hand": dict,       # {'B': int, 'W': int}
    "pieces_on_board": dict,      # {'B': int, 'W': int}
    "move_count": int,            # Movement turns elapsed
    "history": list[tuple],       # (board_state, current_player) history
}
```

**Feedback:** The runner passes `None`. It calls the agent once per turn and
uses a random legal move on failure; there is no retry or invalid-move
feedback dictionary.

#### Constants and Configuration

**Environment Variables:**
- `A8_GAMES_PER_MATCH` (default: 20) — Games per match pairing, read directly
- `A8_MAX_TURNS_PER_GAME` (default: 200) — Movement phase turn limit, independent of Word Matrix's `MAX_TURNS_PER_GAME`
- `MOVE_TIME_LIMIT` (default: 1.0s) — Per-move timeout

**Hardcoded:**
- `GAME_TIME_LIMIT`: 150 × `MOVE_TIME_LIMIT` (see Draw by Time Limit). A match only fails if an agent hangs inside a single move and the hard kill at `GAME_TIME_LIMIT` × games + 60s fires; the runner then exits non-zero so the matchmaker counts it as failed
- Pieces per player: 7
- One placement/movement attempt per turn; failure falls back to a random legal move
- Board size: 24 spots

**Error Handling:**
- Invalid moves: Agent gets feedback, max 3 attempts, then random fallback
- Timeouts: Random fallback
- Crashes: Random fallback
- All errors tracked in match statistics (printed at end)

#### File Locations

**Results:**
- Match logs: `results/surround_morris/<timestamp>_<agent1>_vs_<agent2>_match.txt`
- Global scoreboard: `scoreboard/A8-scoreboard.txt`

**Agents:**
- Generated agents: `agents/<model_folder>/A8-SurroundMorris_<run>.py`

#### Running Matches

**Single match (2 agents):**
```bash
uv run game_scripts/A8-surround_morris_match.py --agent Terra:1 Opus:2
```

**Human play modes:**
```bash
uv run game_scripts/A8-surround_morris_match.py --humanvsbot       # vs random
uv run game_scripts/A8-surround_morris_match.py --humanvshuman    # local 2P
uv run game_scripts/A8-surround_morris_match.py --humanvsagent --agent Terra:1
```

**Tournament (all cross-model pairings):**
```bash
uv run game_scripts/matchmaker.py --game A8 --same_opponent_match 4 --workers 4
```

#### Match Output Format

**Subprocess stdout includes:**
```
RESULT:Agent-1=<pts1>,Agent-2=<pts2>
SCORE:Agent-1=<score1>,Agent-2=<score2>
WINS:Agent-1=<wins1>,Agent-2=<wins2>
DRAWS:<draw_count>
--- MATCH STATISTICS ---
Agent-1 make_move_crash: <count>
Agent-2 make_move_crash: <count>
Agent-1 other_crash: <count>
Agent-2 other_crash: <count>
Agent-1 crash (total): <count>
Agent-2 crash (total): <count>
Agent-1 Captures: <count>
Agent-2 Captures: <count>
Agent-1 Stalemates: <count>
Agent-2 Stalemates: <count>
Total Turns: <count>
Time-limit Draws: <count>
```

**Outer layer parses these lines** via regex to populate result dict and update scoreboard.

---

### A1: Battleship

**Type:** 2-player naval strategy
**Match File:** `game_scripts/A1-battleship_match.py`
**Game Prompt:** `games/A1-Battleship.txt`
**Scoreboard:** `scoreboard/A1-scoreboard.txt`

**Overview:** Classic Battleship on an 8x8 grid. Ships: [5, 4, 3]. Two phases — placement then bombing. Players call shots until all opponent ships are sunk.

**Agent Interface:** `class BattleshipAgent` with `__init__(name, board_size, ships)` and `make_move(state, feedback)` for both phases. Placement returns a dictionary with `ship_length`, `start`, and `orientation`; bombing returns `{'target': (row, col)}`.

**Scoring:** Winner gets +remaining_ship_cells, loser gets -remaining_ship_cells.

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent Terra:1`

---

### A2: LieOnce

**Type:** 2-player number-guessing game with bluffing
**Match File:** `game_scripts/A2-lie_once_match.py`
**Game Prompt:** `games/A2-LieOnce.txt`
**Scoreboard:** `scoreboard/A2-scoreboard.txt`

**Overview:** Each player picks a hidden integer in [1, 100]. Players alternate guessing the opponent's number; the responder must answer "Up", "Down", or "Correct". Each player may lie at most ONCE per game, AND only on their first 10 responses (response 11+ cannot be a lie). A guess wins only when it is genuinely correct AND the responder confirms with "Correct"; if the responder lies and says "Up"/"Down", the lie is consumed and play continues.

**Agent Interface:** `class LieOnceAgent` with three methods:
- `pick_number() -> int` — called once at game start, must return integer in [1, 100].
- `guess(state: dict) -> int` — return integer guess. Non-integer = lose turn; out-of-range integer is legal.
- `respond(state: dict, opponent_guess: int) -> str` — return one of `"Up"`, `"Down"`, `"Correct"`. Anything else = forfeit; second lie = forfeit; lie on response ≥ 11 = forfeit.

**State dict** (passed to both `guess` and `respond`):
```python
{
    "your_number": int,
    "your_lie_used": bool,
    "your_response_count": int,  # responses given so far (lies only legal while < 10)
    "turn": int,                 # 1-indexed combined turn number
    "you_started": bool,
    "is_tie_attempt": bool,
}
```
Agents see ONLY their own state. The runner does not replay history — agents track their own.

**Tie-Attempt:** If the starter wins on turn N (N < 100), the non-starter gets one final guess on turn N+1. Starter responds. If non-starter's guess is genuinely correct AND starter says "Correct" truthfully → DRAW. If starter lies (says "Up"/"Down" with lie still available), the lie is consumed and starter wins (the lie acts as a joker to deny the tie). Second-lie or invalid response in tie → starter forfeits, non-starter wins.

**Starter alternation:** Agent-1 starts game 1, Agent-2 starts game 2, alternating thereafter. Over the default 50 games each agent starts 25 times.

**Scoring:**
- Win = 3 points; tiebreaker score = `100 - winner_guess_count`.
- Loss = 0 points; tiebreaker score = `-(100 - winner_guess_count)`.
- Draw (turn cap or successful tie-attempt) = 1 point each, score 0.
- Forfeit before any guess (e.g. invalid `pick_number`) gives the opponent the maximum score of 100.

**Total turn cap:** 100 combined turns. A non-integer guess still consumes a turn (no feedback exchanged).

**Error Handling:**
- `pick_number` non-integer / out-of-range / crash / timeout → immediate forfeit, opponent score = 100.
- `guess` non-integer / crash / timeout → lose turn (no feedback exchanged); play passes to opponent.
- `respond` invalid string / crash / timeout / second lie → immediate forfeit, opponent treated as having guessed correctly on this turn.

**Game count:** Loads `A2_GAMES_PER_MATCH` directly. Default 50 games per match to sample secret choices and tie-attempt outcomes.

**Human mode:** `--humanvsbot` plays interactively against a random bot.

---

### A3: Wizard

**Status: Playable.**

**Game:** Six players play 10 card rounds. One game includes all 10 rounds.
Placements earn 5/4/3/2/1/0 points; tied players share the points for their positions.
`A3_GAMES_PER_MATCH` controls directly invoked matches (default 24).

**Tournament qualifiers:** Requires exactly two agents per model. Three models
contribute both agents to a six-player table. Each table plays
`A3_QUALIFIER_GAMES_PER_MATCH` games (default 402), then each model keeps its
higher-scoring agent. Every model advances one representative; qualifiers
select agent implementations rather than eliminating models.

**Main event:** Requires at least six models. Each combination of six
representatives plays `A3_MAIN_EVENT_GAMES_PER_MATCH` games (default 6).
For 12 models: four qualifier tables and 924 main-event tables. Each
representative plays 2,772 games across 462 main-event tables. In total the
defaults schedule 1,608 qualifier games and 5,544 main-event games. Seating
rotates within each table across games; all three default counts are multiples
of six, covering each seat equally. Only main-event results
update the global scoreboard. `--dry-run` displays each phase's games per
table and total games; `--auto-yes` skips the prompt between phases.

The two phase counts are independent settings, with no multiplication of a
base count. The current defaults spend many games selecting representatives
at a few qualifier tables and fewer games at each of the many main-event tables.

---

### A4: Backgammon

**Type:** 2-player race game
**Match File:** `game_scripts/A4-backgammon_match.py`
**Game Prompt:** `games/A4-Backgammon.txt`
**Scoreboard:** `scoreboard/A4-scoreboard.txt`

**Overview:** Standard backgammon on a 24-point board. 15 checkers per player, two six-sided dice. White moves toward index 0; Black moves toward index 23. Each subprocess invocation plays one **race-to-5 in-game points**: Single Win = 1 point, Gammon Win = 2 points, turn-limit Draw = 0.5 each. Match (race) caps at `MAX_GAMES_PER_MATCH = 30` for safety. No doubling cube. No Backgammon (3-point) tier.

**Agent Interface:** `class BackgammonAgent` with `make_move(state, feedback)` returning a list of `(from, to)` sub-move tuples. State includes pre-computed `legal_sub_moves` (single-step) and `max_dice_usable` (target sequence length); the returned sequence length must equal `max_dice_usable` exactly.

**Scoring:**
- In-game (per game): Single = 1, Gammon = 2, Draw (turn limit) = 0.5/0.5.
- League (per match): Match Win (first to 5) = 3 points, Match Draw = 1 each, Match Loss = 0.
- Tie-break score = ±(in-game-points diff). E.g., 5–1 in-game → +4/-4.

**Constants:** `MAX_TURNS_PER_GAME = 300`, `POINTS_TO_WIN_MATCH = 5`. `MAX_GAMES_PER_MATCH` reads `A4_MAX_GAMES_PER_MATCH` (default 30); the number of games is variable per race.

**Error handling:** Move crashes, timeouts, and invalid moves are replaced by a random legal turn of exactly `max_dice_usable` sub-moves, using a shared engine planner that backtracks past choices that would leave dice unused. Invalid sequences are rolled back in full before the fallback. The turn counter increments once as usual. Stats track each failure mode separately (`make_move_crash`, `timeout`, `invalid`); hits and dice used include fallback moves. Human modes and the built-in random bot use the same planner. Initialization crashes still forfeit the game (Gammon-equivalent +2 to the opponent).

**Forced-use rule:** Agents must use as many dice as legally possible. The "must play larger die" sub-rule is NOT enforced — if both dice are individually playable but not together, agent picks either.

**Color/turn assignment:** Within each game, White is randomly determined; turn order alternates by color across games (Agent-1 is W in odd-numbered games, B in even).

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent Terra:1`

**Subprocess output extras:** `GAMES_PLAYED:<int>` line is parsed by the outer layer for scoreboard `games_played` (variable per match).

---

### A5: Connect4 (Random Start)

**Type:** 2-player connection game
**Match File:** `game_scripts/A5-connect4_match.py`
**Game Prompt:** `games/A5-Connect4RandomStart.txt`
**Scoreboard:** `scoreboard/A5-scoreboard.txt`

**Overview:** Standard Connect4 on a 6x7 board with one twist: one Red disc is pre-placed at a random column before each game. Yellow makes the first agent decision. Colors alternate between odd/even games.

**Agent Interface:** `class Connect4Agent` with `__init__(name, symbol)` and `make_move(board)` returning a column index (0–6).

**Scoring:** Score = empty cells remaining at win (min 3). Initialization-forfeit score: +35/-35.

**Game count:** Loads `A5_GAMES_PER_MATCH` directly. Default 10 games per match.

**Human mode:** `--human` plays interactively against a random bot.

---

### A6: WordMatrixGame

**Type:** 2-player word path game
**Match File:** `game_scripts/A6-word_matrix_match.py`
**Game Prompt:** `games/A6-WordMatrixGame.txt`
**Scoreboard:** `scoreboard/A6-scoreboard.txt`

**Overview:** 4x4 letter grid. A path uses at least two distinct cells connected horizontally or vertically. Its letters must be a subsequence of a dictionary word, with `len(path) <= len(word) <= 2 * len(path)`. Extra word letters are shuffled back into path cells; the other path cells become empty. Six consecutive passes/failures, no adjacent non-empty cells, or the configured turn cap ends normal play.

**Agent Interface:** `class WordMatrixAgent` with `__init__(name)` and `make_move(board, scores, total_passes)`, returning `(path, word)` or `"PASS"`. A path is a list of `(row, col)` coordinates. The runner supplies `load_words()` for dictionary access.

**Scoring:** 10 base + 10 per cleared cell per word. Invalid move penalty: -10 (no fallback to random). Forfeit score: ±(10 × configured turn cap + 160), or ±1160 at the default 100-turn cap.

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent Terra:1`

---

### A7: Mancala

**Type:** 2-player stone-sowing game
**Match File:** `game_scripts/A7-mancala_match.py`
**Game Prompt:** `games/A7-Mancala.txt`
**Scoreboard:** `scoreboard/A7-scoreboard.txt`

**Overview:** Classic two-rank Mancala. Each player has 6 pockets (4 stones each, 48 total) and a Mancala on their right. A move picks up every stone in one of your pockets and sows them counter-clockwise, one per pocket, dropping into your own Mancala and skipping the opponent's. Long moves (13+ stones) wrap around and drop into the starting pocket too.

- **Free turn:** last stone in your own Mancala → you move again (no limit on chaining).
- **Capture:** last stone in an empty pocket on your own side → that stone and the opposite pocket go to your Mancala. This happens even when the opposite pocket is empty (only your last stone moves). Sowing exactly 13 lands back in the emptied starting pocket and captures.
- **End:** checked after every move. When either row is empty the game ends at once (a pending free turn is cancelled), each player sweeps their own remaining stones into their Mancala, and the bigger Mancala wins. 24-24 is a draw.
- No move-count cap. The tournament runner enforces its separate per-game time limit.

**Random opening and seats:** Before any agent moves, the engine sows a random P1 pocket (logged as `Random opening: P1 pocket N`). It counts as P1's move, so pocket 2 gives P1 a free turn and P1's agent moves next; otherwise P2 does. Agent-1 is P1 in odd games, Agent-2 in even games, and each pair of games (1-2, 3-4, ...) shares one opening, so both agents play both sides of it. With 6 possible openings, a deterministic pair of agents can produce at most 12 distinct games.

**Agent Interface:** `class MancalaAgent` with `__init__(name, player)` (`player` is `'P1'` or `'P2'`) and `make_move(state)` returning a pocket index 0-5. The state is always from the agent's own seat:
```python
{
    "board": list[int],        # 14 ints: 0-5 own pockets, 6 own Mancala,
                               # 7-12 opponent pockets, 13 opponent Mancala
    "legal_moves": list[int],  # own non-empty pockets (never empty)
    "player": str,             # 'P1' or 'P2'
    "move_number": int,        # sowings so far in this game, free turns included
}
```
The engine stores an absolute board (0-5 P1, 6 P1 Mancala, 7-12 P2, 13 P2 Mancala); P2's view is that board rotated by 7. The pocket across from index `i` is `12 - i` in both views. The prompt includes a reference `apply_move(board, pocket)` in the agent's view; `tests/test_mancala.py` checks it against the engine.

**Scoring:** Winner's tie-breaker = own Mancala − opponent's Mancala after the sweep (e.g. 30-18 → +12/-12). Draw = 0. Init-crash forfeit = +48/-48 (the largest possible margin).

**Error handling:** Crash, timeout (1s per `make_move` call, free turns included) or invalid move (not an `int`, outside 0-5, or an empty pocket) → a random legal pocket is played as the agent's move, so it can still earn a free turn or capture. No retries.

**Time limit:** `GAME_TIME_LIMIT` is 25s per game; a game that runs past it ends as a draw. See [Game Time Limits](#game-time-limits).

**Match statistics extras:** `Captures`, `Extra Turns` per agent, `Total Moves`, `Time-limit Draws`.

**Results:** `results/mancala/`. Game count: `A7_GAMES_PER_MATCH` (12 by default), giving six shared-opening pairs with seats swapped. Openings are sampled with replacement, so this does not guarantee all six openings appear.

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent Terra:1`

---

## Agent File Convention

Generated agents saved to: `agents/<sanitized_model_name>/<game_name>_<run_id>.py`

Example: `agents/GPT-6.1-Terra-Extrahigh/A1-Battleship_1.py`

**Model name sanitization** (`utils/populate_agents.py:sanitize_model_name()`): Converts a configured model name into a valid folder name. Current roster names already use valid filename characters and are preserved exactly. Provider-style identifiers, when configured, use these rules:
1. Strip everything after `@` (preset/flavor suffix removed)
2. If the third path segment exists and is not already part of the base name, append it with a hyphen
3. Replace `/` with `-`
4. Replace remaining invalid filesystem characters with `_`

Example: `DeepSeekV4.1-Flash-1017-Max` → `DeepSeekV4.1-Flash-1017-Max`.

**Run ID collision avoidance**: `get_next_run_ids()` scans existing files for the highest run number already present and allocates from `max + 1` onward. Re-running `populate_agents.py` for a model that already has runs will never overwrite them.

**Interactive model resolution**: When `--model <substring>` matches multiple entries in `models.txt`, the CLI presents a numbered menu and prompts the user to select. The command does not silently pick one or fail.

## Matchmaker (Tournament Scheduler)

`game_scripts/matchmaker.py` automates full round-robin tournament execution across all agents for a given game. It discovers agents, generates cross-model fixtures, and runs them concurrently as subprocesses — each delegated to the appropriate game match runner. It can also run a mini league among chosen agents (`--mini`, described below).

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1 through A8 |
| `--same_opponent_match` | int | 8 | Exact match repetitions for each two-player agent pair |
| `--workers` | int | 24 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Preview schedule size and match settings without executing |
| `--new-model` | str | — | Two-player games: comma-separated model folder names; restrict fixtures to those involving these models. Not allowed with `--mini` |
| `--health` | flag | false | Run syntax + broad-except checks on all agents before execution |
| `--random16` | flag | false | Run a random sample of up to 16 matches (2-player games) |
| `--mini` | flag | false | Run a mini league among the agents named in `--agent`, including same-model pairs. Not supported for A3 |
| `--agent` | list | — | Required with `--mini`. `MODEL:RUN` specs (e.g. `GPT-6.1-Terra-Extrahigh:1`), or a single model substring to take all of that model's runs |
| `--auto-yes` | flag | false | Skip confirmation prompts (e.g. A3 Phase 2 start) |

**How `--same_opponent_match` works:**

For two-player games, each cross-model agent pair plays exactly `same_opponent_match` matches. The current 12 models x 2 runs = 24 agents produce 264 cross-model pairings, so `--same_opponent_match 4` schedules 1,056 matches. Mini leagues include same-model pairs. Wizard uses its own two-phase tournament and ignores this option.

**Mini league (`--mini --agent`):**

Runs a league among only the agents you name, instead of every agent in `agents/`. Unlike the tournament, it includes same-model pairs, and each pair plays `--same_opponent_match` times (e.g. 6 agents → 15 pairs × 4 = 60 matches). Mini leagues:
- do **not** pass `--update-scoreboard`, so `scoreboard/` is never changed;
- print a standings table at the end.

```bash
uv run game_scripts/matchmaker.py --game A8 --mini \
  --agent GPT-6.1-Terra-Extrahigh:1 GPT-6.1-Terra-Extrahigh:2 \
          Gemini-Hydrogen-Extrahigh:1 Gemini-Hydrogen-Extrahigh:2 \
          Opus-5.5-Max:1 Opus-5.5-Max:2 \
  --same_opponent_match 4
```

**Incremental tournaments (`--new-model`):** For two-player games, pass model folder names (comma-separated) to generate only fixtures involving those folders. Wizard's separate tournament path does not apply this filter.

**Agent health checks (`--health`):** Before executing, validates every discovered agent for:
1. Syntax validity (`ast.parse`).
2. Broad exception handlers in `make_move` (`except Exception`, `except BaseException`, bare `except:`) — these swallow `MoveTimeoutException` and disable per-move time limits.

**Agent discovery:** Scans `agents/*/` for files matching `{game_name}_{run}.py`. Two-player tournaments generate only cross-model pairings; mini leagues include same-model pairs. Wizard qualifiers seat both runs from each model together, then advance one representative per model.

**Execution:** Each match is a subprocess calling the game's match runner with `--update-scoreboard` appended automatically in tournament mode (mini leagues omit it). The match runner handles game execution, result parsing, scoreboard updates, and log writing internally. The matchmaker only orchestrates scheduling and reports success/failure counts.

**Match counts:** Every game has a dedicated environment variable and independent default in `utils/game_config.py`: A1 20, A2 50, A3 direct 24, A5 10, A6 10, A7 12, A8 20. Wizard qualifiers use 402 games per table and the main event uses six. A4 reads its own cap (default 30) and stops when an agent reaches five points. Counts are read directly with no shared base or division. Dry runs display the effective match counts.

Counts account for draws, randomness, and opening/seat coverage; see README.md
for the rationale. The two-player matchmaker defaults to eight matches per
agent pairing, so total samples per pairing are eight times the configured
count (eight races for Backgammon). Under current scoring each Backgammon race
ends within ten completed games; increasing its cap does not add samples.
Surround Morris has no randomized opening: extra games sample stochastic
agent behavior, but deterministic agents replay the same two seat-swapped
games. More games cannot resolve fixed draws or compensate for restrictive
turn/time limits. These defaults are starting budgets, not measured precision
guarantees for the current agents.

**Timeout:** The matchmaker sets no timeout of its own; it waits for each match subprocess to finish. Each match runner limits every game to its `GAME_TIME_LIMIT` and ends an overrunning game as a draw, so the match still produces a result (see [Game Time Limits](#game-time-limits)). Only a match killed for hanging fails. A7 and A8 then exit non-zero so the matchmaker lists it under Failed; A1-A6 still exit 0.

## Game Time Limits

Each runner defines its own `GAME_TIME_LIMIT` as a multiple of
`MOVE_TIME_LIMIT`. The game clock includes agent setup. During play the runner
checks the clock and ends a game that exceeds its budget as a time-limit draw.
Two-player draws receive 1 league point each and zero tie-breaker score;
Wizard ties all six players (2.5 placement points each); Backgammon awards
0.5 in-game points each. Logs report `Time-limit Draws`.

The table shows source defaults with `MOVE_TIME_LIMIT=1.0`. Environment
settings can override match counts and the move limit.

| Game | Time budget per game | Default games per match | Derived match budget |
|---|---|---|---|
| A1 | 55s | 20 | 1,100s |
| A2 | 35s | 50 | 1,750s |
| A3 direct match | 310s | 24 | 7,440s |
| A3 qualifier | 310s | 402 | 124,620s |
| A3 main event | 310s | 6 | 1,860s |
| A4 | 55s | up to 30 | 1,650s |
| A5 | 30s | 10 | 300s |
| A6 | 15s | 10 | 150s |
| A7 | 25s | 12 | 300s |
| A8 | 150s | 20 | 3,000s |

The match subprocess is killed after the derived match budget plus
`MATCH_KILL_GRACE` (60s). The matchmaker sets no additional timeout. Match
budgets follow the actual game count, including enhancement overrides;
Backgammon uses its configured maximum-game cap. There is no match-timeout
environment setting.

These are configured limits, not measured completion rates for the current
agents. Human modes have game-specific timeout behavior; this table describes
stored-agent benchmark matches.

## Agent Enhancement

`utils/try_enhancing_agents.py` automates iterative improvement of agent quality. For each selected model/game combo, it:

1. Generates 1 new agent (using the same `prompt_model` / `extract_agent_code` pipeline as `populate_agents.py`)
2. Runs same-model matches with 10x that game's configured count (e.g. A1: 200 instead of 20; A5: 100 instead of 10). Backgammon keeps its race-to-five format and configured game cap.
3. Evaluates performance based on match points
4. Prunes the worst agent (new or existing) and renames files to keep run IDs contiguous

**Architecture:** Fully pipelined. All combos run concurrently via `asyncio.gather`. Each combo independently populates → matches → evaluates → prunes. API calls share a semaphore (`MAX_WORKERS`). Match subprocesses share a separate semaphore (capped at 24).

**Worst agent determination:**
- New agent lost to all existing → delete new agent
- New agent beat all existing → run additional old-vs-old matches to find worst existing
- Mixed results → worst is the agent that lost to the new agent with fewest points

**Constraints:**
- Only 2-player games (A3/6-player is excluded automatically)
- Requires ≥ 2 existing agents per model/game combo
- Enhancement matches do not update scoreboards (`--update-scoreboard` is not passed)
- No match timeout of its own: runner limits are per game, so they scale with the 10× game count

**Scheduling:** Enhancement is invoked manually. The repository has no scheduler that automatically runs it every two weeks; Wizard is excluded from enhancement.

## Development Notes

- Match runners execute agents in subprocesses with 1s move timeout (configurable via `MOVE_TIME_LIMIT`)
- Invalid moves, timeouts, crashes fallback to random valid moves
- Game logs track per-agent error statistics
- Agent code injection uses class renaming to avoid conflicts
