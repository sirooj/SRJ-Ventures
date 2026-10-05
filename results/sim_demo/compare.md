# Sim cross-check (FTMO 100k 2-step, dummy strategy)

- ours P(pass all): 0.700 (50 seeded paths, adverse-extreme marking)
- LuxAlgo: Pass probability per attempt                  100.0% (95% CI 100.0â€“100.0%)

Expectation: where trades carry no adverse excursion the two agree within MC
noise; where they differ ours must be lower (LuxAlgo observes equity at trade
close only — see its rule-semantics doc; our open questions in the PR).
Semantic deltas vs our YAMLs: (1) LuxAlgo allows allowance-as-%-of-anchor
(`limitBasis: anchor`) — our schema covers it via `pct_of: reference`, FTMO uses
`initial` on both; (2) their `basis` lacks our max(balance,equity) conservative
superset for The5ers; (3) they model consistency dilution + risk-free min-day
grind, ours fails hard (stricter); (4) failure attribution identical
(higher floor wins).
