import random
from statistics import median, mean

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Phase 1 — Blackjack Simulation Engine
# ---------------------------------------------------------------------------

# Deck: Ace represented as 11; face cards (J, Q, K) as 10
_DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4  # 52 cards

_SHOE_DECKS       = 6
_PENETRATION      = 0.75                          # reshuffle after 75% dealt
_SHOE_SIZE        = len(_DECK) * _SHOE_DECKS      # 312 cards
_RESHUFFLE_THRESH = int(_SHOE_SIZE * (1 - _PENETRATION))  # 78 cards remaining


def fresh_deck():
    """Return a freshly shuffled 52-card deck."""
    deck = _DECK[:]
    random.shuffle(deck)
    return deck


# ---------------------------------------------------------------------------
# Phase 2 — 6-Deck Shoe with Penetration Tracking
# ---------------------------------------------------------------------------

def fresh_shoe():
    """Return a freshly shuffled 6-deck shoe (312 cards)."""
    shoe = _DECK * _SHOE_DECKS
    random.shuffle(shoe)
    return shoe


def needs_reshuffle(shoe):
    """Return True when 75% of the shoe has been dealt (< 78 cards remain)."""
    return len(shoe) < _RESHUFFLE_THRESH


# ---------------------------------------------------------------------------
# Phase 3 — Running Count and True Count
# ---------------------------------------------------------------------------

def update_count(running_count, card, chromosome):
    """
    Add the chromosome-encoded count value for a revealed card to the
    running count and return the updated total.

    running_count : current running count (int)
    card          : raw card value (11=Ace, 2–10)
    chromosome    : 294-bit strategy chromosome
    """
    return running_count + get_count_value(chromosome, card)


def calc_true_count(running_count, remaining_cards):
    """
    Normalise the running count by decks remaining and return the
    rounded integer true count.

    remaining_cards : number of cards left in the shoe
    """
    decks_remaining = remaining_cards / 52
    return round(running_count / decks_remaining)


def hand_value(cards):
    """
    Return (total, is_soft).

    is_soft is True when at least one Ace is still counted as 11.
    If the total exceeds 21, aces are flipped from 11 to 1 as needed.
    """
    total = sum(cards)
    aces = cards.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, aces > 0


def play_hand(strategy_fn, shoe, running_count, chromosome):
    """
    Play one hand of blackjack from a shared shoe.

    strategy_fn(player_total, is_soft, dealer_upcard) -> bool
    shoe          : mutable list of cards; cards are popped as dealt
    running_count : count value carried in from the session
    chromosome    : 294-bit chromosome used to update the running count

    Every revealed card updates the running count via update_count().

    Returns (result, running_count) where result is one of:
        'blackjack' — player natural 21 (pays 3:2)
        'win'       — player beats dealer
        'loss'      — player busts or dealer wins
        'tie'       — equal totals (push)
    """
    # Deal two cards each, alternating as in a real shoe game
    p0 = shoe.pop(); running_count = update_count(running_count, p0, chromosome)
    p1 = shoe.pop(); running_count = update_count(running_count, p1, chromosome)
    d0 = shoe.pop(); running_count = update_count(running_count, d0, chromosome)
    d1 = shoe.pop(); running_count = update_count(running_count, d1, chromosome)

    player       = [p0, p1]
    dealer       = [d0, d1]
    dealer_upcard = d0

    # Check for player blackjack (natural 21 on opening two cards)
    p_total, _ = hand_value(player)
    if p_total == 21:
        d_total, _ = hand_value(dealer)
        result = 'tie' if d_total == 21 else 'blackjack'
        return result, running_count

    # Player turn
    while True:
        p_total, is_soft = hand_value(player)
        if p_total >= 21:
            break
        if not strategy_fn(p_total, is_soft, dealer_upcard):
            break
        card = shoe.pop()
        running_count = update_count(running_count, card, chromosome)
        player.append(card)

    p_total, _ = hand_value(player)
    if p_total > 21:
        return 'loss', running_count

    # Dealer turn: stand on all 17s (S17 rule)
    while True:
        d_total, _ = hand_value(dealer)
        if d_total >= 17:
            break
        card = shoe.pop()
        running_count = update_count(running_count, card, chromosome)
        dealer.append(card)

    d_total, _ = hand_value(dealer)

    if d_total > 21 or p_total > d_total:
        result = 'win'
    elif p_total < d_total:
        result = 'loss'
    else:
        result = 'tie'
    return result, running_count


# ---------------------------------------------------------------------------
# Phase 5 — Session Simulator
# ---------------------------------------------------------------------------

_STARTING_BANKROLL = 1_000
_MIN_BET           = 1
_MAX_BET           = 8
_BJ_PAYOUT         = 3 / 2   # blackjack pays 3:2


def play_session(chromosome, n_hands=1000):
    """
    Simulate a full session of n_hands using the given chromosome.

    Manages the shoe, running count, and bankroll across all hands.
    The shoe is reshuffled (and the count reset) whenever 75% penetration
    is reached after a hand completes.

    Blackjacks pay 3:2; ties are a push (no change to bankroll).
    The session ends early if the bankroll reaches $0.

    Returns (final_bankroll, bankroll_history) where bankroll_history is
    a list of bankroll values recorded after each hand.
    """
    bankroll         = _STARTING_BANKROLL
    shoe             = fresh_shoe()
    running_count    = 0
    strategy_fn      = make_strategy(chromosome)
    bankroll_history = []

    for _ in range(n_hands):
        if bankroll <= 0:
            break

        # Reshuffle if penetration reached
        if needs_reshuffle(shoe):
            shoe          = fresh_shoe()
            running_count = 0

        true_count = calc_true_count(running_count, len(shoe))
        bet        = size_bet(chromosome, true_count, bankroll)

        result, running_count = play_hand(strategy_fn, shoe, running_count, chromosome)

        if result == 'blackjack':
            bankroll += int(bet * _BJ_PAYOUT)
        elif result == 'win':
            bankroll += bet
        elif result == 'loss':
            bankroll -= bet
        # 'tie' → no change

        bankroll_history.append(bankroll)

    return bankroll, bankroll_history


# ---------------------------------------------------------------------------
# Phase 4 — Bet Sizing
# ---------------------------------------------------------------------------

def size_bet(chromosome, true_count, bankroll):
    """
    Determine the bet for the upcoming hand.

    Looks up the bet multiplier for the current true count, computes
    bet = multiplier × $1, then caps at the player's available bankroll.

    Returns an integer bet in the range [1, min(multiplier, bankroll)],
    or 0 if the bankroll is already 0.
    """
    if bankroll <= 0:
        return 0
    multiplier = get_bet_multiplier(chromosome, true_count)
    return min(multiplier, bankroll)


# ---------------------------------------------------------------------------
# Phase 3 — Fitness Evaluation
# (evaluate_fitness defined above, alongside the simulation it depends on)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Validation: hardcoded basic strategy (Wizard of Odds, single-deck, hit/stand)
# ---------------------------------------------------------------------------

def basic_strategy(player_total, is_soft, dealer_upcard):
    """
    Wizard of Odds basic strategy for single-deck blackjack, hit/stand only.
    Returns True to hit, False to stand.
    """
    d = 1 if dealer_upcard == 11 else dealer_upcard  # normalize Ace to 1

    if is_soft:
        if player_total <= 17:
            return True                     # always hit soft 17 or below
        if player_total == 18:
            return d in (9, 10, 1)          # hit vs 9, 10, Ace; stand vs 2–8
        return False                        # stand on soft 19+

    else:
        if player_total <= 8:
            return True                     # always hit
        if player_total in (9, 10, 11):
            return True                     # would double, but hit/stand only
        if player_total == 12:
            return d not in (4, 5, 6)       # stand vs 4–6, hit otherwise
        if 13 <= player_total <= 16:
            return d not in (2, 3, 4, 5, 6) # stand vs 2–6, hit otherwise
        return False                        # hard 17+, always stand


def evaluate_fitness(chromosome, n_hands=1000):
    """
    Evaluate a strategy chromosome by simulating n_hands of blackjack.
    Returns fitness = (wins + 0.5 * ties) / n_hands.
    """
    strategy_fn = make_strategy(chromosome)
    wins = ties = 0
    for _ in range(n_hands):
        result = play_hand(strategy_fn)
        if result == 'win':
            wins += 1
        elif result == 'tie':
            ties += 1
    return (wins + 0.5 * ties) / n_hands


# ---------------------------------------------------------------------------
# Phase 2 — Chromosome Encoding
# ---------------------------------------------------------------------------

# Chromosome layout:
#   Bits   0–169 : hard hands       — player totals 4–20  (17) × dealer upcards (10)
#   Bits 170–259 : soft hands       — soft totals 12–20    (9) × dealer upcards (10)
#   Bits 260–281 : card count vals  — 11 ranks × 2 bits each
#   Bits 282–293 : bet multipliers  —  4 ranges × 3 bits each
#
# Dealer upcard index: Ace=0, 2=1, 3=2, ..., 10=9
#
# Count value encoding (2 bits per rank):
#   00 → -1 | 01 → 0 | 10 → +1 | 11 → 0 (unused, treat as 0)
# Rank order: Ace(11), 2, 3, 4, 5, 6, 7, 8, 9, 10, [spare]
#
# Bet multiplier encoding (3 bits per range, value b → multiplier b+1):
#   Range 0 (tc <= -2)  | Range 1 (-1 to +1) | Range 2 (+2 to +4) | Range 3 (>= +5)

CHROM_LEN    = 294
HARD_OFFSET  = 0
SOFT_OFFSET  = 170
COUNT_OFFSET = 260
BET_OFFSET   = 282

# Rank index for count encoding: Ace(11)→0, 2→1, …, 10→9
_COUNT_RANK_IDX = {11: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9}

# 2-bit decoding table for count values
_COUNT_DECODE = {0: -1, 1: 0, 2: 1, 3: 0}

# True count range → bet multiplier slot index
def _bet_range_idx(true_count):
    if true_count <= -2:
        return 0
    elif true_count <= 1:
        return 1
    elif true_count <= 4:
        return 2
    else:
        return 3


def _dealer_idx(dealer_upcard):
    """Map raw card value to dealer upcard index (Ace→0, 2→1, …, 10→9)."""
    return 0 if dealer_upcard == 11 else dealer_upcard - 1


def _chrom_index(player_total, is_soft, dealer_upcard):
    """Return the chromosome bit index for a given game state."""
    d = _dealer_idx(dealer_upcard)
    if is_soft:
        return SOFT_OFFSET + (player_total - 12) * 10 + d
    else:
        return HARD_OFFSET + (player_total - 4) * 10 + d


def random_chromosome():
    """Return a random 294-bit chromosome (play strategy + count values + bet multipliers)."""
    return [random.randint(0, 1) for _ in range(CHROM_LEN)]


def get_decision(chromosome, player_total, is_soft, dealer_upcard):
    """
    Look up the hit/stand decision for a game state.
    Returns True (hit) or False (stand).
    """
    return bool(chromosome[_chrom_index(player_total, is_soft, dealer_upcard)])


def make_strategy(chromosome):
    """Wrap a chromosome as a strategy_fn compatible with play_hand."""
    def strategy_fn(player_total, is_soft, dealer_upcard):
        return get_decision(chromosome, player_total, is_soft, dealer_upcard)
    return strategy_fn


def chromosome_from_strategy(strategy_fn):
    """
    Encode a strategy function as a chromosome.
    Useful for converting basic_strategy into a chromosome for validation.
    """
    chrom = [0] * CHROM_LEN

    # Hard hands: player totals 4–20
    for total in range(4, 21):
        for dealer_upcard in [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            idx = _chrom_index(total, False, dealer_upcard)
            chrom[idx] = int(strategy_fn(total, False, dealer_upcard))

    # Soft hands: soft totals 12–20
    for total in range(12, 21):
        for dealer_upcard in [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            idx = _chrom_index(total, True, dealer_upcard)
            chrom[idx] = int(strategy_fn(total, True, dealer_upcard))

    return chrom


def get_count_value(chromosome, card_value):
    """
    Decode the count value for a card rank from Component 2 (bits 260–281).

    card_value : raw card value (11=Ace, 2–10)
    Returns    : -1, 0, or +1
    """
    rank_idx = _COUNT_RANK_IDX.get(card_value, 10)   # unknown ranks → spare slot
    bit_pos  = COUNT_OFFSET + rank_idx * 2
    bits     = chromosome[bit_pos] * 2 + chromosome[bit_pos + 1]
    return _COUNT_DECODE[bits]


def get_bet_multiplier(chromosome, true_count):
    """
    Decode the bet multiplier for a true count from Component 3 (bits 282–293).

    true_count : integer true count
    Returns    : multiplier in range 1–8
    """
    bit_pos  = BET_OFFSET + _bet_range_idx(true_count) * 3
    bits     = chromosome[bit_pos] * 4 + chromosome[bit_pos + 1] * 2 + chromosome[bit_pos + 2]
    return bits + 1   # 0–7 → 1–8


# ---------------------------------------------------------------------------
# Phase 4 — Genetic Algorithm
# ---------------------------------------------------------------------------

POP_SIZE      = 100
GENERATIONS   = 100
N_HANDS       = 1000
MUTATION_RATE = 0.005


def crossover(p1, p2):
    """Single-point crossover. Returns two children."""
    point = random.randint(1, CHROM_LEN - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


def mutate(chromosome, rate=MUTATION_RATE):
    """Flip each bit independently with probability rate."""
    return [bit ^ 1 if random.random() < rate else bit for bit in chromosome]


def run_ga(pop_size=POP_SIZE, generations=GENERATIONS,
           n_hands=N_HANDS, mutation_rate=MUTATION_RATE):
    """
    Run the genetic algorithm.

    Returns (final_population, history) where history is a list of dicts
    with keys 'min', 'max', 'median', 'mean' for each generation evaluated.
    """
    population = [random_chromosome() for _ in range(pop_size)]
    history = []

    for gen in range(generations):
        # Evaluate fitness for every individual
        fitness_scores = [evaluate_fitness(c, n_hands) for c in population]

        # Record per-generation stats
        history.append({
            'min':    min(fitness_scores),
            'max':    max(fitness_scores),
            'median': median(fitness_scores),
            'mean':   mean(fitness_scores),
        })

        print(
            f"Gen {gen + 1:3d}/{generations} | "
            f"min={history[-1]['min']:.4f}  "
            f"max={history[-1]['max']:.4f}  "
            f"median={history[-1]['median']:.4f}  "
            f"mean={history[-1]['mean']:.4f}"
        )

        # Rank population by fitness (descending)
        ranked = sorted(zip(fitness_scores, population),
                        key=lambda x: x[0], reverse=True)
        weights = [f for f, _ in ranked]
        chroms  = [c for _, c in ranked]

        # Elitism: top 2 advance unchanged
        next_gen = [chroms[0], chroms[1]]

        # Fill the rest via roulette wheel selection, crossover, mutation
        while len(next_gen) < pop_size:
            p1, p2 = random.choices(chroms, weights=weights, k=2)
            c1, c2 = crossover(p1, p2)
            next_gen.append(mutate(c1, mutation_rate))
            if len(next_gen) < pop_size:
                next_gen.append(mutate(c2, mutation_rate))

        population = next_gen

    return population, history


# ---------------------------------------------------------------------------
# Phase 5 — Output
# ---------------------------------------------------------------------------

_DEALER_UPCARDS = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]
_DEALER_LABELS  = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']
_HARD_TOTALS    = list(range(4, 21))   # 17 rows
_SOFT_TOTALS    = list(range(12, 21))  # 9 rows
_SOFT_LABELS    = ['A-A', 'A-2', 'A-3', 'A-4', 'A-5',
                   'A-6', 'A-7', 'A-8', 'A-9']


def _hit_grid(population, totals, is_soft):
    """Return a 2-D array of hit fractions (rows=player totals, cols=dealer upcards)."""
    n = len(population)
    return np.array([
        [sum(get_decision(c, t, is_soft, d) for c in population) / n
         for d in _DEALER_UPCARDS]
        for t in totals
    ])


def plot_fitness(history, save_path='fitness_over_generations.png'):
    """Figure 1: min/max/median/mean fitness over generations."""
    gens = list(range(1, len(history) + 1))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(gens, [h['min']    for h in history], label='Min',    color='steelblue',  linestyle='--')
    ax.plot(gens, [h['max']    for h in history], label='Max',    color='firebrick',  linestyle='--')
    ax.plot(gens, [h['median'] for h in history], label='Median', color='darkorange', linewidth=2)
    ax.plot(gens, [h['mean']   for h in history], label='Mean',   color='seagreen',   linewidth=2)
    ax.axhline(0.480, color='gray', linestyle=':', linewidth=1, label='Basic strategy (~0.480)')

    ax.set_xlabel('Generation')
    ax.set_ylabel('Fitness (Win Rate)')
    ax.set_title('Blackjack GA — Fitness Over Generations')
    ax.legend()
    ax.set_ylim(0.28, 0.54)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {save_path}")


def plot_strategy_heatmap(population, save_path='strategy_heatmap.png'):
    """Figure 2: hit-percentage heat map for hard and soft hands."""
    hard_grid = _hit_grid(population, _HARD_TOTALS, is_soft=False)
    soft_grid = _hit_grid(population, _SOFT_TOTALS, is_soft=True)

    cmap = plt.cm.RdBu_r   # blue = stand (0%), red = hit (100%)

    fig, axes = plt.subplots(1, 2, figsize=(16, 9), layout='constrained')

    panels = [
        (axes[0], hard_grid, [str(t) for t in _HARD_TOTALS], 'Hard Hands'),
        (axes[1], soft_grid, _SOFT_LABELS,                    'Soft Hands'),
    ]

    for ax, grid, row_labels, title in panels:
        im = ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect='auto')

        ax.set_xticks(range(10))
        ax.set_xticklabels(_DEALER_LABELS, fontsize=9)
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=9)
        ax.set_xlabel('Dealer Upcard', fontsize=10)
        ax.set_ylabel('Player Hand',   fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold')

        # Annotate each cell with the hit percentage
        for r in range(grid.shape[0]):
            for c in range(grid.shape[1]):
                pct = int(round(grid[r, c] * 100))
                text_color = 'white' if abs(grid[r, c] - 0.5) > 0.3 else 'black'
                ax.text(c, r, str(pct), ha='center', va='center',
                        fontsize=7, color=text_color, fontweight='bold')

    fig.colorbar(im, ax=axes, orientation='vertical', fraction=0.02, pad=0.04,
                 label='% of Population Recommending Hit')
    fig.suptitle('Blackjack GA — Final Population Strategy\n(Blue = Stand, Red = Hit)',
                 fontsize=13)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print(f"Running GA: {GENERATIONS} generations, "
          f"pop={POP_SIZE}, {N_HANDS} hands/eval\n")

    final_pop, history = run_ga()

    best_fitness = max(evaluate_fitness(c, n_hands=10_000) for c in final_pop)
    print(f"\nBest individual fitness (10k hands): {best_fitness:.4f}")
    print(f"Final generation — "
          f"min={history[-1]['min']:.4f}  "
          f"max={history[-1]['max']:.4f}  "
          f"median={history[-1]['median']:.4f}  "
          f"mean={history[-1]['mean']:.4f}")

    print("\nGenerating figures...")
    plot_fitness(history)
    plot_strategy_heatmap(final_pop)
    print("Done.")
