"""Curated Benchmark Challenge Problems for LLM Code & Reasoning Evaluation."""

from typing import List
from codeeval.models import Category, Difficulty, Problem, TestCase


def get_all_benchmark_problems() -> List[Problem]:
    """Returns the curated benchmark dataset designed to expose LLM reasoning flaws."""

    problems: List[Problem] = [
        # -------------------------------------------------------------------------
        # Problem 1: Constrained Subsequence Sum (Monotonic Queue DP)
        # -------------------------------------------------------------------------
        Problem(
            id="eval-dp-001",
            title="Constrained Subsequence Maximum Sum",
            description=(
                "Given an integer array 'nums' and an integer 'k', return the maximum sum of a "
                "non-empty subsequence of that array such that for every two consecutive integers in "
                "the subsequence, nums[i] and nums[j], their original index difference (j - i) <= k.\n"
                "Constraints: 1 <= nums.length <= 10^5, -10^4 <= nums[i] <= 10^4, 1 <= k <= nums.length."
            ),
            entry_point="constrained_subset_sum",
            category=Category.DYNAMIC_PROGRAMMING,
            difficulty=Difficulty.HARD,
            constraints=[
                "1 <= len(nums) <= 10^5",
                "-10^4 <= nums[i] <= 10^4",
                "1 <= k <= len(nums)",
                "Time Complexity: O(N) using Monotonic Deque or O(N log K)",
                "Space Complexity: O(N)",
            ],
            time_limit_seconds=2.0,
            common_pitfalls=[
                "Naive O(N*K) solution times out on large N (10^5).",
                "Handling all negative numbers: subsequence must be non-empty, so result must be max(nums) not 0.",
                "Off-by-one errors when maintaining deque window of size k (indices > i - k).",
            ],
            golden_solution="""
from collections import deque

def constrained_subset_sum(nums, k):
    n = len(nums)
    dp = [0] * n
    q = deque()  # stores indices of dp in decreasing order of value

    ans = nums[0]
    for i in range(n):
        # Remove out-of-window elements (distance > k)
        while q and q[0] < i - k:
            q.popleft()

        max_prev = dp[q[0]] if q else 0
        dp[i] = nums[i] + max(0, max_prev)
        ans = max(ans, dp[i])

        # Maintain decreasing order in deque
        while q and dp[q[-1]] <= dp[i]:
            q.pop()
        q.append(i)

    return ans
""".strip(),
            test_cases=[
                TestCase(
                    inputs={"nums": [10, 2, -10, 5, 20], "k": 2},
                    expected_output=37,
                    is_hidden=False,
                    description="Standard case with mixed positive/negative values",
                ),
                TestCase(
                    inputs={"nums": [-1, -2, -3], "k": 1},
                    expected_output=-1,
                    is_hidden=False,
                    description="All negative elements (must select non-empty max element)",
                ),
                TestCase(
                    inputs={"nums": [10, -2, -10, -5, 20], "k": 2},
                    expected_output=23,
                    is_hidden=False,
                    description="Jump over multiple negative numbers",
                ),
                TestCase(
                    inputs={"nums": [5], "k": 1},
                    expected_output=5,
                    is_hidden=True,
                    description="Single element array boundary test",
                ),
                TestCase(
                    inputs={"nums": [-100, -200, -50, -300], "k": 2},
                    expected_output=-50,
                    is_hidden=True,
                    description="All negative array where max is at an inner index",
                ),
                TestCase(
                    inputs={"nums": [1] * 5000, "k": 10},
                    expected_output=5000,
                    is_hidden=True,
                    timeout_seconds=2.0,
                    description="Large linear scale test to detect O(N*K) asymptotic regressions",
                ),
            ],
        ),
        # -------------------------------------------------------------------------
        # Problem 2: Directed Graph Cycle Detection & Lexicographical Ordering
        # -------------------------------------------------------------------------
        Problem(
            id="eval-graph-002",
            title="Directed Graph Cycle Detection and Path Lexicography",
            description=(
                "Given a directed graph represented by 'num_nodes' (0 to num_nodes - 1) and a list of 'edges' [u, v],\n"
                "determine if a cycle exists. If a cycle exists, return the lexicographically smallest cycle as a list\n"
                "of node IDs starting and ending at the same minimum node (e.g., [1, 3, 2, 1]).\n"
                "If no cycle exists, return a valid topological sort order as a list of integers."
            ),
            entry_point="evaluate_graph_dependencies",
            category=Category.GRAPH_ALGORITHMS,
            difficulty=Difficulty.HARD,
            constraints=[
                "1 <= num_nodes <= 10^4",
                "0 <= len(edges) <= 2 * 10^4",
                "Graph may be disconnected",
            ],
            time_limit_seconds=2.0,
            common_pitfalls=[
                "Failing to handle disconnected components with separate cycles.",
                "Returning invalid cycle rotation (must start and end at the cycle's minimum node).",
                "Handling self-loops correctly: [u, u] -> cycle is [u, u].",
                "Recursion limit exceeded on deep linear graphs without iterative / colored DFS.",
            ],
            golden_solution="""
from collections import defaultdict, deque

def evaluate_graph_dependencies(num_nodes, edges):
    adj = defaultdict(list)
    in_degree = [0] * num_nodes
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1

    for u in adj:
        adj[u].sort()

    # Cycle detection via colored DFS
    visited = [0] * num_nodes  # 0=unvisited, 1=visiting, 2=visited
    parent = {}
    found_cycles = []

    def dfs(u, path):
        visited[u] = 1
        path.append(u)
        for v in adj[u]:
            if visited[v] == 1:
                # Cycle found from v to u
                idx = path.index(v)
                cycle = path[idx:] + [v]
                found_cycles.append(cycle)
            elif visited[v] == 0:
                dfs(v, path)
        path.pop()
        visited[u] = 2

    for node in range(num_nodes):
        if visited[node] == 0:
            dfs(node, [])

    if found_cycles:
        # Standardize cycles to start and end at minimum node
        normalized_cycles = []
        for c in found_cycles:
            raw = c[:-1]
            min_val = min(raw)
            min_idx = raw.index(min_val)
            rotated = raw[min_idx:] + raw[:min_idx] + [min_val]
            normalized_cycles.append(rotated)
        normalized_cycles.sort()
        return normalized_cycles[0]

    # No cycle: produce topological sort (Kahn's Algorithm)
    pq = [i for i in range(num_nodes) if in_degree[i] == 0]
    pq.sort()
    topo = []
    q = deque(pq)
    while q:
        curr = q.popleft()
        topo.append(curr)
        for nxt in adj[curr]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                q.append(nxt)

    return topo
""".strip(),
            test_cases=[
                TestCase(
                    inputs={"num_nodes": 4, "edges": [[0, 1], [1, 2], [2, 0], [2, 3]]},
                    expected_output=[0, 1, 2, 0],
                    is_hidden=False,
                    description="Simple 3-node cycle with outgoing branch",
                ),
                TestCase(
                    inputs={"num_nodes": 3, "edges": [[0, 1], [1, 2]]},
                    expected_output=[0, 1, 2],
                    is_hidden=False,
                    description="DAG with unambiguous linear topological order",
                ),
                TestCase(
                    inputs={"num_nodes": 2, "edges": [[1, 1]]},
                    expected_output=[1, 1],
                    is_hidden=True,
                    description="Self-loop boundary test",
                ),
                TestCase(
                    inputs={"num_nodes": 4, "edges": []},
                    expected_output=[0, 1, 2, 3],
                    is_hidden=True,
                    description="Completely disconnected empty edge graph",
                ),
            ],
        ),
        # -------------------------------------------------------------------------
        # Problem 3: Robust Log Tokenizer with Nested Escapes
        # -------------------------------------------------------------------------
        Problem(
            id="eval-string-003",
            title="Nested Escaped Log Stream Tokenizer",
            description=(
                "Implement a parser function 'tokenize_log_stream(stream)' that breaks a raw log stream into clean tokens.\n"
                "Rules:\n"
                "1. Tokens are separated by whitespace (spaces, tabs).\n"
                "2. Tokens enclosed in double quotes (\"\") or square brackets ([]) must be kept as single tokens, with enclosing delimiters removed.\n"
                "3. Backslash escaping (\\) preserves the literal value of the next character (including quotes, brackets, and spaces).\n"
                "4. Consecutive adjacent duplicate tokens must be deduplicated into a single instance (case-sensitive).\n"
                "5. Return the resulting list of tokens."
            ),
            entry_point="tokenize_log_stream",
            category=Category.STRING_PARSING,
            difficulty=Difficulty.MEDIUM,
            constraints=[
                "0 <= len(stream) <= 10^5",
                "Stream contains printable ASCII characters",
            ],
            time_limit_seconds=2.0,
            common_pitfalls=[
                "Unescaped quotes splitting tokens incorrectly.",
                "Failing to handle consecutive backslashes (e.g. '\\\\').",
                "Empty string input raising IndexError or returning [''].",
                "Failing to deduplicate adjacent matching tokens while preserving non-adjacent duplicates.",
            ],
            golden_solution="""
def tokenize_log_stream(stream):
    if not stream:
        return []

    tokens = []
    curr = []
    i = 0
    n = len(stream)
    in_quote = False
    in_bracket = False

    while i < n:
        ch = stream[i]

        if ch == '\\\\' and i + 1 < n:
            curr.append(stream[i + 1])
            i += 2
            continue

        if ch == '"' and not in_bracket:
            in_quote = not in_quote
            i += 1
            continue

        if ch == '[' and not in_quote and not in_bracket:
            in_bracket = True
            i += 1
            continue

        if ch == ']' and in_bracket and not in_quote:
            in_bracket = False
            i += 1
            continue

        if ch.isspace() and not in_quote and not in_bracket:
            if curr:
                tokens.append("".join(curr))
                curr = []
            i += 1
            continue

        curr.append(ch)
        i += 1

    if curr:
        tokens.append("".join(curr))

    # Adjacent deduplication
    deduped = []
    for t in tokens:
        if not deduped or deduped[-1] != t:
            deduped.append(t)

    return deduped
""".strip(),
            test_cases=[
                TestCase(
                    inputs={"stream": 'INFO [auth service] "user login successful" INFO'},
                    expected_output=["INFO", "auth service", "user login successful", "INFO"],
                    is_hidden=False,
                    description="Standard log message with quotes and brackets",
                ),
                TestCase(
                    inputs={"stream": "WARN WARN ERROR ERROR WARN"},
                    expected_output=["WARN", "ERROR", "WARN"],
                    is_hidden=False,
                    description="Deduplication of consecutive identical tokens",
                ),
                TestCase(
                    inputs={"stream": ""},
                    expected_output=[],
                    is_hidden=True,
                    description="Empty string boundary test",
                ),
                TestCase(
                    inputs={"stream": 'key="value with \\"quotes\\" and \\\\slash"'},
                    expected_output=['key=value with "quotes" and \\slash'],
                    is_hidden=True,
                    description="Nested backslash escaping inside quoted string",
                ),
            ],
        ),
        # -------------------------------------------------------------------------
        # Problem 4: Sliding Window Rate Limiter
        # -------------------------------------------------------------------------
        Problem(
            id="eval-algo-004",
            title="Sliding Window Rate Limiter with Penalty Cooldown",
            description=(
                "Implement a class-level simulation function 'simulate_rate_limiter(requests, max_requests, window_size, penalty_cooldown)'.\n"
                "Requests is a list of timestamps in milliseconds.\n"
                "A request is allowed if there are strictly fewer than 'max_requests' in the last 'window_size' milliseconds.\n"
                "If a request is rejected, the client enters a penalty cooldown period where all requests are rejected until\n"
                "'penalty_cooldown' milliseconds have passed since the LAST rejected request timestamp.\n"
                "Return a list of booleans indicating whether each request in 'requests' was accepted (True) or rejected (False)."
            ),
            entry_point="simulate_rate_limiter",
            category=Category.DATA_STRUCTURES,
            difficulty=Difficulty.MEDIUM,
            constraints=[
                "0 <= len(requests) <= 10^5",
                "Timestamps are non-decreasing",
                "max_requests >= 1, window_size >= 1, penalty_cooldown >= 0",
            ],
            time_limit_seconds=2.0,
            common_pitfalls=[
                "Updating penalty timer on subsequent requests while already in cooldown.",
                "Off-by-one errors in window expiration (< vs <=).",
                "Handling empty requests list gracefully.",
            ],
            golden_solution="""
from collections import deque

def simulate_rate_limiter(requests, max_requests, window_size, penalty_cooldown):
    if not requests:
        return []

    accepted_timestamps = deque()
    results = []
    cooldown_until = -1

    for t in requests:
        # Check if in cooldown
        if t < cooldown_until:
            cooldown_until = t + penalty_cooldown
            results.append(False)
            continue

        # Evict timestamps outside sliding window
        while accepted_timestamps and accepted_timestamps[0] <= t - window_size:
            accepted_timestamps.popleft()

        if len(accepted_timestamps) < max_requests:
            accepted_timestamps.append(t)
            results.append(True)
        else:
            cooldown_until = t + penalty_cooldown
            results.append(False)

    return results
""".strip(),
            test_cases=[
                TestCase(
                    inputs={
                        "requests": [100, 200, 300, 400, 500, 1200],
                        "max_requests": 3,
                        "window_size": 1000,
                        "penalty_cooldown": 500,
                    },
                    expected_output=[True, True, True, False, False, True],
                    is_hidden=False,
                    description="Standard sequence triggering cooldown and subsequent recovery",
                ),
                TestCase(
                    inputs={
                        "requests": [],
                        "max_requests": 5,
                        "window_size": 1000,
                        "penalty_cooldown": 200,
                    },
                    expected_output=[],
                    is_hidden=True,
                    description="Empty requests list",
                ),
                TestCase(
                    inputs={
                        "requests": [1000, 1000, 1000, 1000],
                        "max_requests": 2,
                        "window_size": 100,
                        "penalty_cooldown": 50,
                    },
                    expected_output=[True, True, False, False],
                    is_hidden=True,
                    description="Simultaneous requests at identical millisecond",
                ),
            ],
        ),
    ]

    return problems
