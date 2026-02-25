import random

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

    # Dealer turn: stand on hard 17+, hit on soft 17 and below
    while True:
        d_total, d_soft = hand_value(dealer)
        if d_total > 17 or (d_total == 17 and not d_soft):
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


def evaluate_fitness(strategy_fn, n_hands=1000):
    """Simulate n_hands and return fitness score."""
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
# Validation
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    n = 100_000
    print(f"Phase 1 — basic strategy function over {n:,} hands:")
    fitness = evaluate_fitness(basic_strategy, n_hands=n)
    print(f"  Win rate: {fitness:.4f}  (target: ~0.480)\n")

    print(f"Phase 2 — chromosome-encoded basic strategy over {n:,} hands:")
    bs_chrom = chromosome_from_strategy(basic_strategy)
    fitness_chrom = evaluate_fitness(make_strategy(bs_chrom), n_hands=n)
    print(f"  Win rate: {fitness_chrom:.4f}  (should match Phase 1)\n")

    print("Chromosome spot-checks (basic strategy):")
    checks = [
        (8,  False, 10, True,  "hard 8 vs 10 → hit"),
        (17, False,  6, False, "hard 17 vs 6 → stand"),
        (12, False,  5, False, "hard 12 vs 5 → stand"),
        (12, False,  3, True,  "hard 12 vs 3 → hit"),
        (16, False,  7, True,  "hard 16 vs 7 → hit"),
        (18, True,   9, True,  "soft 18 vs 9 → hit"),
        (18, True,   6, False, "soft 18 vs 6 → stand"),
    ]
    for total, soft, dealer, expected, label in checks:
        decision = get_decision(bs_chrom, total, soft, dealer)
        status = "OK" if decision == expected else "FAIL"
        print(f"  [{status}] {label}")
