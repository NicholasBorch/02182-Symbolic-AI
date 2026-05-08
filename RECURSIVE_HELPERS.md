# Recursive Helper Agents - Implementation Guide

## Overview

The goal recognition system now supports **recursive helper planning**, where each helper plans on top of the previous helper's AND-OR contingency plan. This enables solving problems like the tunnel scenario where Helper 2 must move an outer box before Helper 1 can move an inner box.

## Architecture

### State Representation

- **Helper 1**: `GoalRecognitionNode(physical_state, solution_graph)`
  - `solution_graph` is the actor's All-Optimal-Plans solution graph
  - Tracks nondeterminism from the actor's rational actions
  
- **Helper N (N ≥ 2)**: `HelperNGoalRecognitionNode(physical_state, helper_(N-1)_plan_node)`
  - `helper_(N-1)_plan_node` is the current node in the previous helper's AND-OR plan
  - Nondeterminism comes from both the actor AND the previous helper's choices

### AND-OR Search for Each Helper

**Helper 1 (existing)**:
- OR-nodes: Helper 1 chooses action `a₁`
- AND-nodes: Branch on actor's percepts from `solution_graph`
- State transitions through `solution_graph_results(state, joint_action)`

**Helper N (new)**:
- OR-nodes: Helper N chooses action `aₙ`
- AND-nodes: Branch on actor's percepts (from original `solution_graph`)
  - For each actor percept `a₀`:
    1. Look up Helper(N-1)'s action `a_{N-1}` from `helper_(N-1)_policy[current_node]`
    2. Compute `Result(s, a₀ | a₁ | ... | a_{N-1} | aₙ)` 
    3. Advance Helper(N-1) plan node by calling `results_fn(node, joint_action)`
    4. New state = `(new_physical_state, new_helper_(N-1)_node)`

### Key Classes

```python
class HelperNGoalRecognitionNode:
    state: State                    # Physical world state
    helper_prev_node: GoalRecognitionNode | HelperNGoalRecognitionNode
```

### Key Functions

```python
def make_helper_n_results(helper_level, prev_helper_policy, prev_helper_results_fn=None):
    """Factory that creates the results function for Helper N"""
    # Returns a function that:
    # 1. Gets previous helper's action from policy
    # 2. Gets actor percepts from solution_graph
    # 3. For each percept: computes new state and advances prev helper's plan
    # 4. Returns list of new Helper N states
```

## Execution Flow

1. **Planning Phase** (top-level):
   - Extract actor and helper colors from level
   - Run All-Optimal-Plans for actor to get `solution_graph`
   - Create Helper 1 root: `GoalRecognitionNode(initial_state, solution_graph)`
   - Run AND-OR search → get `helper1_policy`
   - Create Helper 2 root: `HelperNGoalRecognitionNode(initial_state, helper1_root)`
   - Run AND-OR search with `helper_2_results_fn` → get `helper2_policy`
   - (Repeat for Helper 3, 4, ...)

2. **Execution Phase** (goal achievement loop):
   - Query `helper1_policy[current_gr_node]` → get helper 1's action
   - Choose actor action from solution_graph choices
   - Execute joint action for all agents
   - Track position in each helper's plan by:
     - Getting outcomes from results function
     - Finding the outcome matching the actual actor action
     - Updating `current_helper_n_node` to the next plan node

## Agent Color Assignment

- Actor: color at `initial_agent_positions[0]`
- Helper 1: color at `initial_agent_positions[1]`
- Helper 2: color at `initial_agent_positions[2]`
- etc.

## Tunnel Example Scenario

Level has 2 agents (actor + helper) where:
- Inner box is where actor needs to go
- Outer box blocks the path
- Outer box can only be moved by helper

**Solution**:
1. Actor's All-Optimal-Plans computes: "Actor must move inner box"
2. Helper 1 realizes: "To move inner box, I must first move outer box"
3. Helper 1's AND-OR plan: 
   - OR-node: I can move outer box OR wait
   - AND-branches: For each actor percept (after I move outer box, actor can move inner)
4. During execution:
   - Helper 1 moves outer box
   - Actor moves inner box
   - Goal achieved!

## Design Decisions

1. **Nondeterminism Source**: Always from actor's `solution_graph`, never reinvented
   - ✅ Clean: Single source of truth about what actor might do
   - ✅ Correct: Based on actor's color-blind optimal planning

2. **Recursive State Chaining**: `Helper N` stores pointer to `Helper(N-1)` node
   - ✅ Minimal: Only track what's necessary to advance previous helper's plan
   - ✅ Navigable: Can always look up previous helper's action and advance

3. **Results Function Factory**: Each Helper N gets a closure over prev helper's policy
   - ✅ Clean: Captures policy at planning time
   - ✅ Efficient: No extra state passed during AND-OR search

## Limitations

- Actor is always agent 0 (index 0)
- Helpers are always indices 1, 2, ... in assignment order
- Each helper sees full solution_graph (for now) — could be filtered per color
- No pruning based on helper goals (planned for future)
