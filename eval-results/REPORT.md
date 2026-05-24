# Phase 1 results

## Per-package

| Package | Model | n | coverage | no-skill | skill | Lift |
|---|---|---|---|---|---|---|
| arrow | sonnet | 15 | 15/15 | 14/15 (93%) | 12/15 (80%) | -13.3pp |
| arrow | haiku | 15 | 15/15 | 13/15 (87%) | 13/15 (87%) | +0.0pp |
| pendulum | sonnet | 12 | 12/12 | 12/12 (100%) | 12/12 (100%) | +0.0pp |
| pendulum | haiku | 12 | 12/12 | 11/12 (92%) | 12/12 (100%) | +8.3pp |
| mcp | sonnet | 15 | 15/15 | 3/15 (20%) | 15/15 (100%) | +80.0pp |
| mcp | haiku | 15 | 15/15 | 13/15 (87%) | 15/15 (100%) | +13.3pp |
| fastmcp | sonnet | 18 | 18/18 | 9/18 (50%) | 17/18 (94%) | +44.4pp |
| fastmcp | haiku | 18 | 18/18 | 13/18 (72%) | 18/18 (100%) | +27.8pp |
| h3 | sonnet | 18 | 18/18 | 18/18 (100%) | 18/18 (100%) | +0.0pp |
| h3 | haiku | 18 | 18/18 | 8/18 (44%) | 18/18 (100%) | +55.6pp |
| returns | sonnet | 15 | 15/15 | 12/15 (80%) | 14/15 (93%) | +13.3pp |
| returns | haiku | 15 | 15/15 | 11/15 (73%) | 14/15 (93%) | +20.0pp |
| msgspec | sonnet | 15 | 15/15 | 12/15 (80%) | 14/15 (93%) | +13.3pp |
| msgspec | haiku | 15 | 15/15 | 15/15 (100%) | 15/15 (100%) | +0.0pp |
| more_itertools | sonnet | 15 | 15/15 | 2/15 (13%) | 7/15 (47%) | +33.3pp |
| more_itertools | haiku | 15 | 15/15 | 3/15 (20%) | 12/15 (80%) | +60.0pp |

## Aggregate

| Model | Packages | Total items | no-skill | skill | Lift |
|---|---|---|---|---|---|
| sonnet | 8 | 123 | 82/123 (66.7%) | 109/123 (88.6%) | +22.0pp |
| haiku | 8 | 123 | 87/123 (70.7%) | 117/123 (95.1%) | +24.4pp |

## Residual skill misses (model + skill still got it wrong)

### arrow (sonnet) — 3 misses
- expected `arrow.get` — got 'arrow.Arrow.fromtimestamp', expected 'arrow.get'
  task: Convert the Unix timestamp 1748080800 to an Arrow datetime, using the arrow libr...
- expected `arrow.ArrowFactory` — got 'arrow.factory', expected 'arrow.ArrowFactory'
  task: Using the arrow library, create an ArrowFactory instance to produce arrow dateti...
- expected `arrow.ArrowFactory` — got 'arrow.factory', expected 'arrow.ArrowFactory'
  task: Construct an arrow ArrowFactory bound to a custom Arrow-derived class for specia...

### arrow (haiku) — 2 misses
- expected `arrow.get` — got 'arrow.parser.DateTimeParser', expected 'arrow.get'
  task: With the arrow library, parse the date string '2026/05/24 10:00' according to a ...
- expected `arrow.ArrowFactory` — got 'arrow.api.factory', expected 'arrow.ArrowFactory'
  task: Using the arrow library, create an ArrowFactory instance to produce arrow dateti...

### fastmcp (sonnet) — 1 misses
- expected `fastmcp.Context` — got None, expected 'fastmcp.Context'
  task: Using fastmcp, create the Context type used to expose framework state inside too...

### returns (sonnet) — 1 misses
- expected `returns.converters.flatten` — got None, expected 'returns.converters.flatten'
  task: Flatten a nested Maybe[Maybe[int]] container into a single Maybe[int] via the re...

### returns (haiku) — 1 misses
- expected `returns.functions.identity` — got None, expected 'returns.functions.identity'
  task: Using returns, get the identity function (returns its argument unchanged) via re...

### msgspec (sonnet) — 1 misses
- expected `msgspec.Meta` — got None, expected 'msgspec.Meta'
  task: With msgspec, declare an Annotated field carrying a Meta object that specifies v...

### more_itertools (sonnet) — 8 misses
- expected `more_itertools.interleave` — got 'more_itertools.roundrobin', expected 'more_itertools.interleave'
  task: Using more_itertools, interleave the elements of three lists [1,2,3], [4,5,6], [...
- expected `more_itertools.interleave` — got 'more_itertools.roundrobin', expected 'more_itertools.interleave'
  task: Round-robin interleave several iterables, terminating when the shortest is exhau...
- expected `more_itertools.interleave` — got 'more_itertools.roundrobin', expected 'more_itertools.interleave'
  task: With more_itertools, take one element from each of multiple iterables in alterna...
- expected `more_itertools.roundrobin` — got 'more_itertools.interleave_longest', expected 'more_itertools.roundrobin'
  task: With more_itertools, walk multiple iterables in round-robin order, continuing pa...
- expected `more_itertools.roundrobin` — got 'more_itertools.interleave_longest', expected 'more_itertools.roundrobin'
  task: Interleave several iterables of differing lengths via more_itertools, taking tur...
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: Using more_itertools, run-length-encode the iterable ['a','a','a','b','b','c'] i...
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: With more_itertools, produce a run-length encoding of a sequence as (value, run_...
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: Compute a run-length encoded representation of a sequence of repeating values us...

### more_itertools (haiku) — 3 misses
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: Using more_itertools, run-length-encode the iterable ['a','a','a','b','b','c'] i...
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: With more_itertools, produce a run-length encoding of a sequence as (value, run_...
- expected `more_itertools.run_length` — got 'more_itertools.run_length.encode', expected 'more_itertools.run_length'
  task: Compute a run-length encoded representation of a sequence of repeating values us...
