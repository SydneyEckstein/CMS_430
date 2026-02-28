# Project 3: Blackjack Strategy Evolution with Genetic Algorithms

## Overview

Blackjack, sometimes known as 21, is the most popular table game played in American casinos. The object is to obtain a hand of cards that scores higher than the dealer's hand without going over a score of 21.

In this project, you'll use genetic programming to evolve a strategy for blackjack. Your strategy will specify under what circumstances the player should hit or stand. You'll score the fitness of each strategy by playing simulated hands of blackjack, then use the genetic algorithm technique to evolve new strategies that descend from the current top performers. The overall goal is to evolve a strategy that performs close to the theoretically optimal win rate of approximately 49.5%.

> **Disclaimer:** These projects are for educational purposes only. They are not an endorsement of gambling.

---

## Rules

Our version of blackjack only allows the player to **hit or stand**. We won't consider alternative moves like doubling, splitting, surrendering, or side bets like insurance. Every decision is a binary choice.

This project focuses on **single-deck blackjack**, which is generally more favorable to the player. Most Vegas casinos now use 6 or 8 decks to reduce the impact of card counting.

- Each hand is dealt from a freshly shuffled standard 52-card deck
- Dealer stands on soft 17
- Player may only hit or stand — no doubling, splitting, or insurance
- A tie (push) counts as 0.5 wins
- Blackjacks (natural 21) count as wins

---

## Strategy

### Basic Strategy

The Wizard of Odds' basic blackjack strategy serves as our reference and target. Each decision depends on exactly two things: the player's current hand total and the dealer's face-up card.

**Hard hands** (no ace, or ace counted as 1):
- Hard 8 or less — always hit
- Hard 17 or more — always stand
- Hard 12–16 — stand if dealer shows 2–6 (dealer likely to bust), hit against 7–Ace
- Hard 9–11 — generally hit

**Soft hands** (ace counted as 11):
- Soft 17 or less — always hit (the ace provides a safety net)
- Soft 18 — stand against weak dealers (2–8), hit against strong dealers (9–Ace)
- Soft 19–20 — always stand

### Chromosome Encoding

Each individual encodes a complete playing strategy as a **260-bit binary chromosome**:

- **Hard hands — 170 bits**: player totals 4–20 (17 values) × dealer upcard Ace–10 (10 values)
- **Soft hands — 90 bits**: player totals Soft 12–20 (9 values) × dealer upcard Ace–10 (10 values)

Each bit represents the decision for one player-dealer combination: `0` = Stand, `1` = Hit.

### Fitness Function

Fitness is evaluated by simulating **5,000 hands** with the encoded strategy:

```
fitness = (wins + 0.5 × ties) / (wins + losses + ties)
```

---

## Phased Implementation

**Phase 1 — Blackjack Simulation Engine**
Build the core game logic independently of the GA. Implement hand evaluation with correct soft/hard ace logic, a full hand loop with dealer behavior (hits on soft 17), and result classification. Validate by hardcoding the basic strategy and confirming ~49.5% win rate over a large sample.

**Phase 2 — Chromosome Encoding**
Design the 260-bit chromosome with a clean index mapping for both hard and soft hands. Implement a single `get_decision(chromosome, total, is_soft, dealer_upcard)` lookup function. Validate by re-encoding basic strategy and re-running the simulator.

**Phase 3 — Fitness Evaluation**
Wire the simulation to the chromosome. Simulate 5,000 hands per individual and return the fitness score using the wins/ties/losses formula.

**Phase 4 — Genetic Algorithm Loop**
Initialize 150 random strategy vectors. For each of 150 generations: evaluate fitness, preserve the top 5 elites, fill the remaining 145 slots via roulette wheel selection, single-point crossover, and per-bit mutation at rate 0.01.

**Phase 5 — Output and Analysis**
Generate the two output figures and compare the evolved population's consensus strategy against the Wizard of Odds basic strategy table.

---

## Desired Output

### Figure 1: Fitness Over Generations
A line plot with **generation** on the horizontal axis and **fitness (win rate)** on the vertical axis. Four lines show the **min, max, median, and mean** fitness across the population each generation. The plot should show convergence toward approximately 49.5%.

### Figure 2: Strategy Heat Map
Two panels — one for hard hands (17×10 grid) and one for soft hands (9×10 grid) — showing for each player hand / dealer upcard combination the **percentage of individuals in the final population that recommend hitting**.

- Pure **red** = 100% hit
- Pure **blue** = 100% stand
- Gradient shading for intermediate values

The heat map should visually agree with the Wizard of Odds basic strategy, confirming that the GA discovered the correct play for each situation from random initialization.
