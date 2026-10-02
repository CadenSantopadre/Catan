# Catan Economics

An experimental Python implementation of Settlers of Catan designed to explore resource allocation, trading behavior, and heuristic decision-making through simulation.

## Overview

Catan Economics models a Catan-like game environment with a procedurally generated board, player inventories, resource production, construction, and player-to-player trading.

The long-term goal is to investigate how resource scarcity, opportunity cost, and strategic incentives influence trading decisions.

## Current Features

- **Board generation:** Creates a hexagonal board with randomized terrain and number tokens.
- **Game state:** Tracks players, resources, victory points, and the resource bank.
- **Resource production:** Distributes resources based on dice rolls and player buildings.
- **Heuristic decision-making:** Assigns scores to construction actions.
- **Trading system:** Generates trade proposals based on resource urgency and evaluates offers using player-specific rules.
- **Resource urgency:** Estimates how urgently a player needs each resource.
- **Production analysis:** Calculates a player's production power for each resource using the probability weights of adjacent number tokens.
- **Visualization:** Displays the board and plots resource inventories, urgency, victory points, hand sizes, bank supplies, and estimated scarcity.

## Technology

- Python
- NumPy
- Matplotlib
- Dataclasses

## Current Model

The simulation uses heuristic rules to approximate player decisions.

Resource urgency currently depends on inventory thresholds and the resource requirements for settlements and cities. Production power is estimated from the number tokens adjacent to a player's buildings.

The trading model is experimental. Its opportunity-cost calculations and acceptance rules are still under development.

## Current Limitations

- The trading heuristics have not been validated against human player behavior.
- Resource valuation does not yet capture the full strategic context of a game.
- The AI uses hand-designed rules rather than a learned policy.
- The game implementation is incomplete and may not enforce every official Catan rule.
- Results from individual simulated games are not sufficient to establish general behavioral patterns.

## Next Steps

1. Debug trade proposal and acceptance logic.
2. Validate resource accounting and game-state transitions.
3. Improve resource valuation using production, inventory, and building objectives.
4. Implement multiple AI strategies for comparison.
5. Log trade proposals, acceptances, rejections, and game states.
6. Run repeated simulations with controlled strategy variations.
7. Compare simulated behavior against observations from human games.

## Research Direction

The broader research question is how resource values and trading decisions change with game state.

Potential variables include resource production rates, inventory levels, resource scarcity, distance from completing a build, and opponents' victory points.

Future experiments could compare rule-based agents and evaluate whether their trading patterns reproduce behaviors observed in human Catan games.