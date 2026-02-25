# Card Counting — Phased Implementation Spec

## Overview

Extend `blackjack_ga.py` into a card counting system. The GA now evolves three things simultaneously: a hit/stand strategy (same as before), a card counting system (how much each rank is worth), and a bet-sizing strategy (how much to wager at each count level).

Total chromosome length: **294 bits** (260 + 22 + 12)

---

## Phase 1 — Extended Chromosome Encoding

Extend the chromosome with two new components appended after the existing 260-bit play strategy.

### Component 2: Card Count Values (bits 260–281, 22 bits)

Encode a count value `{-1, 0, +1}` for each of 11 card values using 2 bits per rank:

| Bits | Value |
|------|-------|
| 00   | -1    |
| 01   |  0    |
| 10   | +1    |
| 11   | treat as 0 |

Ranks encoded (in order): Ace, 2, 3, 4, 5, 6, 7, 8, 9, 10, and one additional slot (per the 22-bit spec). All ten-valued cards (10, J, Q, K) share the same count value.

**Functions to implement:**
- `get_count_value(chromosome, card_value) -> int` — decode the 2-bit encoding for a given card value and return -1, 0, or +1.

### Component 3: Bet Multipliers (bits 282–293, 12 bits)

Encode a bet multiplier (1–8) for each of four true count ranges using 3 bits. A 3-bit value `b` maps to multiplier `b + 1` (so `000` → 1, `111` → 8).

| True Count Range | Bit offset within component |
|------------------|-----------------------------|
| <= -2            | 282–284                     |
| -1 to +1         | 285–287                     |
| +2 to +4         | 288–290                     |
| >= +5            | 291–293                     |

**Functions to implement:**
- `get_bet_multiplier(chromosome, true_count) -> int` — look up the decoded multiplier (1–8) for the given true count.

### Updates to existing helpers
- Update `CHROM_LEN` from 260 to 294.
- Update `random_chromosome()` to produce 294 random bits.

---

## Phase 2 — 6-Deck Shoe with Penetration Tracking

Replace the single-deck `fresh_deck()` with a 6-deck shoe and add penetration logic.

**Functions to implement:**
- `fresh_shoe() -> list` — return a shuffled list of 312 cards (6 copies of the 52-card deck).
- `needs_reshuffle(shoe) -> bool` — return `True` when 75% of the shoe has been dealt (i.e., fewer than 78 cards remain, meaning ≥ 234 have been dealt).

The shoe is passed into and mutated by each hand (cards are popped as they are dealt). When `needs_reshuffle` is True after a hand completes, replace the shoe with a fresh one and reset the running count to 0.

---

## Phase 3 — Running Count and True Count

Maintain a running count across hands within a single shoe.

**Functions to implement:**
- `update_count(running_count, card, chromosome) -> int` — add the chromosome-encoded count value for `card` to `running_count` and return the new total. Called every time a card is revealed (player cards, dealer upcard, dealer hole card, and any hit cards).
- `calc_true_count(running_count, remaining_cards) -> int` — compute:
  ```
  decks_remaining = remaining_cards / 52
  true_count = round(running_count / decks_remaining)
  ```
  Return the rounded integer true count.

---

## Phase 4 — Bet Sizing

At the start of each hand, determine the wager.

**Function to implement:**
- `size_bet(chromosome, true_count, bankroll) -> int` — look up the bet multiplier via `get_bet_multiplier`, compute `bet = multiplier × $1`, and cap at `min(bet, bankroll)`. Return the integer bet amount.

---

## Phase 5 — Extended Game Simulation

Replace `play_hand` with a full session simulator that manages bankroll, the shoe, and the running count across 1,000 hands.

### Updated `play_hand` signature
```python
play_hand(strategy_fn, shoe, running_count, chromosome) -> (result, bet, running_count)
```
- Deals from the provided `shoe` (mutates it in place).
- Updates `running_count` for every revealed card.
- Applies 3:2 payout for player blackjack (e.g., a $2 bet returns $3 profit).
- Returns the hand result (`'win'`, `'loss'`, `'tie'`, `'blackjack'`), the bet amount, and the updated running count.

### `play_session`
```python
play_session(chromosome, n_hands=1000) -> (final_bankroll, bankroll_history)
```
- Starts with bankroll = $1,000, a fresh shoe, and running_count = 0.
- Each hand:
  1. If `needs_reshuffle(shoe)`, replace shoe and reset running count.
  2. Compute true count, size the bet.
  3. If bankroll == 0, stop early and return 0.
  4. Play the hand, update bankroll.
  5. Record bankroll after each hand.
- Returns the final bankroll and the full list of per-hand bankroll values.

---

## Phase 6 — Fitness Function

Replace the old win-rate fitness with a bankroll-based fitness.

```python
evaluate_fitness(chromosome, n_hands=1000) -> float
```
- Call `play_session` and return the final bankroll.
- If the bankroll hits $0 before all hands are played, return 0.

---

## Phase 7 — Genetic Algorithm

Reuse the GA structure from `blackjack_ga.py` with minimal changes:

- `CHROM_LEN` is now 294.
- All other GA parameters (population size, generations, mutation rate, elitism, roulette selection, single-point crossover) remain the same.
- The fitness values are now dollar amounts (~$1,000 scale) rather than fractions; roulette selection still works correctly since `random.choices` normalizes weights.

> Note: if any chromosome has bankrupt fitness (0), it may receive no selection weight. Consider adding a floor (e.g., `max(fitness, 1)`) to avoid zero-weight individuals stalling selection.

---

## Phase 8 — Output

Produce four outputs.

### Output 1: Fitness Line Plot
Same as `blackjack_ga.py` but with the y-axis showing bankroll ($) instead of win rate. Plot min, max, median, and mean fitness per generation.

### Output 2: Strategy Heat Map
Identical to `blackjack_ga.py` — hard and soft hand hit percentages across the final population.

### Output 3: Evolved Count Values vs. Hi-Lo
For the best individual in the final population, decode its Component 2 bits and display a comparison table:

| Rank | Hi-Lo | Evolved |
|------|-------|---------|
| 2    |  +1   |   ?     |
| 3    |  +1   |   ?     |
| 4    |  +1   |   ?     |
| 5    |  +1   |   ?     |
| 6    |  +1   |   ?     |
| 7    |   0   |   ?     |
| 8    |   0   |   ?     |
| 9    |   0   |   ?     |
| 10   |  -1   |   ?     |
| Ace  |  -1   |   ?     |

Print or display this table in the terminal output and/or save as part of a figure.

### Output 4: Bet Multipliers Table
For the best individual, decode Component 3 and display:

| True Count Range | Multiplier |
|------------------|------------|
| <= -2            |     ?      |
| -1 to +1         |     ?      |
| +2 to +4         |     ?      |
| >= +5            |     ?      |

### Output 5: Bankroll Trajectory Plot
Run one fresh 1,000-hand session using the best individual and plot bankroll (y-axis) vs. hand number (x-axis). Helps visualize variance and the effect of bet sizing.

---

## File Checklist

| Item | Status |
|------|--------|
| Extended chromosome (294 bits) | [ ] |
| `get_count_value` | [ ] |
| `get_bet_multiplier` | [ ] |
| `fresh_shoe` + `needs_reshuffle` | [ ] |
| `update_count` + `calc_true_count` | [ ] |
| `size_bet` | [ ] |
| Updated `play_hand` (shoe, count, 3:2 BJ) | [ ] |
| `play_session` | [ ] |
| `evaluate_fitness` (bankroll-based) | [ ] |
| GA loop (updated for 294-bit chromosome) | [ ] |
| Fitness line plot | [ ] |
| Strategy heat map | [ ] |
| Count values vs. Hi-Lo table | [ ] |
| Bet multipliers table | [ ] |
| Bankroll trajectory plot | [ ] |
