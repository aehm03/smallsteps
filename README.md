# Babysteps - improve your codebase in baby steps

Babysteps allows you to declare ratchets – metrics that must increase over time – and to enforce them via testing or CI pipelines.

A typical situation: you want to add test coverage as a health check.
Initially your coverage is at 42% so you create a CI gate that fails if it falls under 40%. Now you have your baseline secured – so far so good. You make a resolution to yourself that you will increase your coverage to bump up the percentage in your CI action frequently.
**Somehow that never happens and your coverage stays at 42%.**

With babysteps you declare your goal of 80% coverage and that you want to reach it in 100 days. Babysteps computes the necessary percentage that must be met for each day (e.g. after 50 days you need 60% coverage) and fails if the goal is not met.

## Example

We are using this repository itself as an example. We want to enforce our test coverage to go up.
So we create a ratchet:

```
uvx babysteps add \
  --name="Pytest Coverage" \
  --command="uv run pytest --cov --cov-report=json > /dev/null && jq -r '.totals.percent_covered' coverage.json" \
  --goal=80 \
  --end="2026-10-01"
```

This created a new file – `babysteps.toml` – which holds the configuration of our ratchet:

```toml
# BabySteps Configuration

[[ratchets]]
name = "Pytest Coverage"
start = 2026-06-25
end = 2026-10-01
initial_value = 57.142857142857146
goal_value = 80
command = "uv run pytest --cov --cov-report=json > /dev/null && jq -r '.totals.percent_covered' coverage.json"

```

**Note**

- You don't need to memorize the command parameters, `babysteps add` walks you through them interactively.
- Ratchets can be increasing or decreasing. Percentages (56%) are parsed as floats (.56). So make sure that your goal matches the format of the command output.

You can inspect, add or modify the ratchets using the the toml file.

### Checking your Ratchets

Run `uvx babysteps check` to check the status of your ratchets. To simulate the future you can run with `--date`, e.g.:

```
uv babysteps check --date 2026-10-31
Evaluating 1 ratchet(s)...

Pytest Coverage: BEHIND (Current: 57.14, Expected Min: 80.00)

Progress check failed.

```

shows that on the goal date the check will fail if we do not achieve 80% test coverage.

### CI and reading values from env

When running `babysteps check` all commands to gather your metrics are run by babysteps. This may be not the desired behaviour in CI because you want to run the checks in different workflows / actions and do not want to use babysteps as a central orchestrator.

By default babysteps looks for environment variables matching the ratchets before running the command. E.g. if `BABYSTEPS_PYTEST_COVERAGE` is present, the coverage is not re-computed. You can use this in CI to pass outputs from test workflow into the babysteps action. To get a scaffolding github action with the required input vars for your ratchets run `uvx babysteps ci`.

Have a look at [the action](.github/actions/babysteps/action.yml) and the whole workflow (not provided by a command because too specific for your setup) to see how the plumbing can work.

## Installation

This documentaion assumes you are using `uv`, hence you don't need to do anything despite using the uv tool command (`ux`) to install and run babysteps.
