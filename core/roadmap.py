"""
CONSIS 8-Week Roadmap Module
----------------------------
Defines the 56-day (8-week) Dual-Pattern Interleaving cycle.
Each week pairs one Primary/Anchor pattern (70% focus) with a
Subsidiary/Support pattern (30% focus).
"""

ROADMAP = [
    {
        "week": 1,
        "primary": "Sliding Window",
        "subsidiary": "Two Pointers",
        "default_bridge": "Use Sliding Window when elements are contiguous; use Two Pointers when sorted order allows shrinking or expanding from ends."
    },
    {
        "week": 2,
        "primary": "Prefix Sum",
        "subsidiary": "Hash Map",
        "default_bridge": "Use Prefix Sum for O(1) range sum queries; combine with Hash Map to detect target subarray sums in O(N) time."
    },
    {
        "week": 3,
        "primary": "Monotonic Stack",
        "subsidiary": "Next Greater Element",
        "default_bridge": "Use Monotonic Stack to maintain monotonic order; use Next Greater Element pattern to find nearest dominant boundaries."
    },
    {
        "week": 4,
        "primary": "Top K (Heaps)",
        "subsidiary": "Quickselect",
        "default_bridge": "Use Heap for dynamic or streaming Top-K tracking; use Quickselect for O(N) average time on static arrays."
    },
    {
        "week": 5,
        "primary": "BFS",
        "subsidiary": "Queue / Level Order",
        "default_bridge": "Use BFS for shortest path in unweighted graphs or grids; use Queue to process level-by-level state transitions."
    },
    {
        "week": 6,
        "primary": "DFS",
        "subsidiary": "Backtracking",
        "default_bridge": "Use DFS for exhaustive path exploration; use Backtracking state reset to prune invalid branches early."
    },
    {
        "week": 7,
        "primary": "Matrix Traversal",
        "subsidiary": "Direction Arrays & Boundary Checks",
        "default_bridge": "Use Matrix Traversal for 2D grids; use direction vectors (dx, dy) and boundary guard logic for clean neighbor traversal."
    },
    {
        "week": 8,
        "primary": "DP Patterns",
        "subsidiary": "Memoization & Table Transitions",
        "default_bridge": "Use Memoization for top-down recursive subproblems; use Table Transitions for bottom-up space-optimized dynamic programming."
    }
]

FOCUS_TYPES = {
    1: "anchor_deep_dive",
    2: "anchor_drill",
    3: "subsidiary_deep_dive",
    4: "connection_bridge",
    5: "mixed_problem",
    6: "recall_test",
    7: "next_week_preview"
}


def get_day_context(cycle_day_index: int) -> dict:
    """
    Given a 0-indexed day counter, computes:
    - cycle_number (1, 2, ...)
    - week_number (1..8)
    - day_in_week (1..7)
    - primary & subsidiary patterns
    - focus type for today
    - default connection bridge
    - next week's primary pattern
    """
    total_days = len(ROADMAP) * 7  # 56 days
    cycle_number = (cycle_day_index // total_days) + 1
    day_in_cycle = cycle_day_index % total_days

    week_index = day_in_cycle // 7
    day_in_week = (day_in_cycle % 7) + 1

    current_week = ROADMAP[week_index]
    next_week = ROADMAP[(week_index + 1) % len(ROADMAP)]

    return {
        "cycle_number": cycle_number,
        "week_number": current_week["week"],
        "day_in_week": day_in_week,
        "primary": current_week["primary"],
        "subsidiary": current_week["subsidiary"],
        "focus": FOCUS_TYPES[day_in_week],
        "default_bridge": current_week["default_bridge"],
        "next_primary": next_week["primary"],
    }
