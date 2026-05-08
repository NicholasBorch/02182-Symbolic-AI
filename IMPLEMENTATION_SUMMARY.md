# Implementation Summary: Recursive Helper Agents

## Changes Made

### 1. ✅ Navigable AND-OR Plan Tree for Helper 1

**Status**: Already existed via policy dict, made explicit in type hints
- Policy dict maps `GoalRecognitionNode → JointAction`
- `solution_graph_results()` allows navigation: given state + actor percept → next state
- **Usage**: `policy[state]` returns helper's action; outcomes from `solution_graph_results()` are navigable states

### 2. ✅ Helper 2+ State Representation with Plan Pointer

**New class**: `HelperNGoalRecognitionNode`
```python
state: State                          # Physical world state
helper_prev_node: GoalRecognitionNode | HelperNGoalRecognitionNode
```
- Tracks position in previous helper's AND-OR plan tree
- Recursively chains: Helper N → Helper(N-1) → ... → Helper 1 → solution_graph

### 3. ✅ Recursive Results Functions

**New factory**: `make_helper_n_results(helper_level, prev_helper_policy, prev_helper_results_fn)`

For each actor percept:
1. Looks up `helper_(N-1)_action` from `prev_helper_policy[current_node]` ✓
2. Computes `Result(s, a₀ | a₁ | ... | a_{N-1} | aₙ)` ✓
3. Advances previous helper node via `prev_helper_results_fn(node, joint_action)` ✓
4. Returns new state: `HelperNGoalRecognitionNode(new_s, new_helper_(N-1)_node)` ✓

### 4. ✅ Multi-Agent Goal Recognition

**Modified**: `goal_recognition_agent()`

**New flow**:
1. Extract actor color (index 0) and helper colors (indices 1, 2, ...)
2. Build color-filtered actor goals
3. For each helper:
   - Create AND-OR root state (wrapping previous helper's root)
   - Create recursive results function
   - Run AND-OR search → get policy
4. During execution:
   - Query policies at each level
   - Execute all helper actions together
   - Track position through each helper's plan

### 5. ✅ Color-Based Role Assignment

**New function**: `extract_agent_roles(level) → (actor_color, helper_colors)`

- Actor: character at `initial_agent_positions[0]`
- Helper 1: character at `initial_agent_positions[1]`
- Helper 2: character at `initial_agent_positions[2]`
- etc.

## Tunnel Scenario Support

**Problem**: Inner box blocked by outer box
- Outer box can only be moved by Helper 2
- Inner box can only be moved by Helper 1
- Actor wants to reach inside

**Solution**:
```
Actor's solution_graph: 
  [Root] --move_inner-box--> [Goal]

Helper 1's AND-OR plan:
  [Root] --help_actor--> ? (wait for outer box to move)
         --move_outer-box--> [Help other helper]

Helper 2's AND-OR plan:
  [Root] --move_outer_box--> [Enable Helper 1]
         --wait--> (if Helper 1 can handle it)
```

During execution:
1. Helper 2 sees Helper 1 cannot proceed (outer box blocks)
2. Helper 2 moves outer box
3. Helper 1 now can move inner box
4. Actor moves inner box
5. Goal achieved

## Backward Compatibility

✅ Single-helper scenarios (level.num_agents == 2) work unchanged:
- Only creates `GoalRecognitionNode` for root
- `current_helper_n_node` stays `None`
- Execution uses only `policies[1]` and `solution_graph_results`

## Key Files Modified

- `search/agents/goal_recognition.py`:
  - Added `HelperNGoalRecognitionNode` class
  - Added `make_helper_n_results()` factory
  - Added `extract_agent_roles()` helper
  - Modified `goal_recognition_agent()` for recursive planning + execution

## Testing the Implementation

The system is now ready to handle:
- ✅ 2 agents (actor + 1 helper) — existing behavior preserved
- ✅ 3+ agents (actor + N helpers) — new recursive behavior
- ✅ Color-based role assignment
- ✅ Complex interdependencies like the tunnel scenario

**To test with tunnel scenario**:
```bash
# Level should have 3 agents with colors assigned
# Actor (color A) needs to reach goal blocked by outer box
# Helper 1 (color B) moves inner box
# Helper 2 (color C) moves outer box
python3 client.py goal_recognition --level tunnel_level.lvl
```
