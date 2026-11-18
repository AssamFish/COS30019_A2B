# A2B routing scenario tests

These 15 synthetic networks isolate search behavior with controlled link travel
times in seconds. They extend the real road-network and data-processing tests.
Each case runs through RoadNetwork.find_top_k_routes with all six A2A algorithms.

The longest fixed test route has 45 sites and 44 links. The dense complex case
contains 128 possible loopless routes. These are bounded test cases, and the
application continues to recommend routes by its selected search strategy.

| Scenario file | Purpose |
|---|---|
| [complex_network](../tests/scenarios/complex_network.json) | Dense directed network with 128 distinct loopless routes. |
| [cycles](../tests/scenarios/cycles.json) | Road cycles must never create repeated sites in a result. |
| [dead_end](../tests/scenarios/dead_end.json) | The lowest-ID branch ends without reaching the destination. |
| [direct_link](../tests/scenarios/direct_link.json) | A single road connects start to destination. |
| [equal_times](../tests/scenarios/equal_times.json) | Two alternatives have equal total travel time. |
| [five_alternatives](../tests/scenarios/five_alternatives.json) | Five distinct routes must be returned out of six available. |
| [greedy_trap](../tests/scenarios/greedy_trap.json) | Geographically closer branch has a higher travel-time cost. |
| [long_chain](../tests/scenarios/long_chain.json) | Longest fixed test chain with 45 sites and 44 compulsory links. |
| [nonconsecutive_sites](../tests/scenarios/nonconsecutive_sites.json) | SCATS IDs are labels and may have large gaps. |
| [one_way_blocked](../tests/scenarios/one_way_blocked.json) | A road cannot be traversed against its direction. |
| [origin_is_goal](../tests/scenarios/origin_is_goal.json) | Staying at the same site returns zero travel time. |
| [parallel_links](../tests/scenarios/parallel_links.json) | Duplicate road entries use the cheapest directed link. |
| [unreachable](../tests/scenarios/unreachable.json) | Destination exists in a disconnected component. |
| [weighted_detour](../tests/scenarios/weighted_detour.json) | A three-link route is quicker than the direct road. |
| [zero_time_link](../tests/scenarios/zero_time_link.json) | Zero-cost links remain valid without causing a loop. |


## Expected behavior

Every result must follow existing directed links, have the correct summed cost,
avoid repeated sites and respect the requested route count. An independent
exhaustive enumeration supplies the valid routes for these bounded fixtures.

A* and CUS1 must return minimum-cost alternatives in cost order. BFS and CUS2
must return alternatives in minimum-hop order. DFS must retain its deterministic
depth-first ordering. GBFS must follow its heuristic in the explicit greedy
trap case, where the nearer-looking branch costs more. DFS and GBFS have
no minimum-travel-time guarantee.

## Recorded results

All 90 scenario and algorithm combinations passed. The CSV records the first
path, its travel time in seconds, returned route count, search nodes created and
runtime. Runtime depends on the computer used.

Run these commands from the project folder.

```powershell
python -m unittest discover -v
python -m tests.test_search_scenarios
```

The second command refreshes [search_scenario_results.csv](search_scenario_results.csv).
The original A2A test suite also passed all 17 scenarios across six algorithms,
giving 102 runs.

## Real workbook integration check

For GRU, 30 October 2006 at 08:00, origin 2000 and destination 3002, the first
returned route was checked through each algorithm and full driving validation.

| Algorithm | Minutes | Search nodes created |
|---|---:|---:|
| DFS | 21.62 | 14 |
| BFS | 20.66 | 81 |
| GBFS | 21.14 | 18 |
| AS | 20.66 | 90 |
| CUS1 | 20.66 | 177 |
| CUS2 | 20.66 | 55 |

With multiple routes requested, the GUI ranks the selected algorithm's returned
candidates by their validated estimated time. This ranking can differ from
algorithm discovery order. Search counts measure generated search-tree nodes,
including the origin and repeated states reached through different paths.


## Real-route demonstration in the main GUI

Use **Test route (15 real trips)** directly below **Search algorithm**. Each preset
fills real SCATS endpoints and an October 2006 departure. Click **Find routes** to
run the chosen traffic model, search method and complete driving validation on
the main street map. See `data/roads/test-routes.json` for all preset settings.
The synthetic networks above are automated regression fixtures.

The real presets include a longest modeled trip, central alternatives, short
and reverse trips, corridor journeys, morning/midday/evening and weekend cases,
the brief's example, and an identical-origin/destination case. The longest case
maximizes shortest-road distance across pairs in the prepared network.
