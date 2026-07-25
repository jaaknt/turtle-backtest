"""Bulk (all-tickers-at-once) research implementations backing the scripts/ studies.

These modules mirror the per-ticker production strategies in ``turtlex/strategy/``
but load the whole universe in a single query, which is what the parameter sweeps
in ``scripts/`` need. Parity with the production path is enforced by tests.
"""
