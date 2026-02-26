import random
from statistics import median, mean

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Phase 1 — Blackjack Simulation Engine
# ---------------------------------------------------------------------------

# Deck: Ace represented as 11; face cards (J, Q, K) as 10
_DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4  # 52 cards


def fresh_deck():
    """Return a freshly shuffled 52-card deck."""
    deck = _DECK[:]
    random.shuffle(deck)
    return deck


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


def play_hand(strategy_fn):
    """
    Play one hand of blackjack using the given strategy function.

    strategy_fn(player_total: int, is_soft: bool, dealer_upcard: int) -> bool
        Returns True to hit, False to stand.
        dealer_upcard is the raw card value (11 = Ace, 2–10 otherwise).

    Returns 'win', 'loss', or 'tie'.
    """
    deck = fresh_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    dealer_upcard = dealer[0]

    # Check for player blackjack (natural 21 on opening two cards)
    p_total, _ = hand_value(player)
    if p_total == 21:
        d_total, _ = hand_value(dealer)
        return 'tie' if d_total == 21 else 'win'

    # Player turn
    while True:
        p_total, is_soft = hand_value(player)
        if p_total >= 21:
            break
        if not strategy_fn(p_total, is_soft, dealer_upcard):
            break
        player.append(deck.pop())

    p_total, _ = hand_value(player)
    if p_total > 21:
        return 'loss'

    # Dealer turn: stand on all 17s (S17 rule)
    while True:
        d_total, _ = hand_value(dealer)
        if d_total >= 17:
            break
        dealer.append(deck.pop())

    d_total, _ = hand_value(dealer)

    if d_total > 21 or p_total > d_total:
        return 'win'
    elif p_total < d_total:
        return 'loss'
    else:
        return 'tie'


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
#   Bits   0–169 : hard hands  — player totals 4–20  (17) × dealer upcards (10)
#   Bits 170–259 : soft hands  — soft totals 12–20   (9)  × dealer upcards (10)
#
# Dealer upcard index: Ace=0, 2=1, 3=2, ..., 10=9

CHROM_LEN = 260
HARD_OFFSET = 0
SOFT_OFFSET = 170


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
    """Return a random 260-bit strategy chromosome."""
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


# ---------------------------------------------------------------------------
# Phase 4 — Genetic Algorithm
# ---------------------------------------------------------------------------

POP_SIZE      = 150
GENERATIONS   = 150
N_HANDS       = 5000
MUTATION_RATE = 0.01


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

        # Elitism: top 5 advance unchanged
        next_gen = chroms[:5]

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
