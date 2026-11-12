"""Simulated LLM Submission: Constrained Subsequence Maximum Sum.
Contains two classic frontier model flaws:
1. Returns 0 on all-negative arrays (subsequence must be non-empty).
2. Naive O(N * K) nested loop leading to Time Limit Exceeded on large test cases.
"""

def constrained_subset_sum(nums, k):
    # Bug 1: Initializing answer to 0 instead of max(nums)
    ans = 0
    n = len(nums)
    dp = list(nums)

    # Bug 2: O(N * K) brute force dynamic programming
    for i in range(n):
        for j in range(max(0, i - k), i):
            dp[i] = max(dp[i], nums[i] + dp[j])
        ans = max(ans, dp[i])

    return ans
