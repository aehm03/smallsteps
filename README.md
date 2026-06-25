# Smallsteps - improve your codebase in small steps

Smallsteps allows you to declare ratchets – metrics that must increase over time – and to enforce them via testing or CI pipelines.

A typical situation: you want to add test coverage as a health check.
Initially your coverage is at 42% so you create a CI gate that fails if it falls under 40%. Now you have your baseline secured – so far so good. You make a resolution to yourself: you will increase your coverage and bump up the minimum percentage frequently.
**Somehow that never happens and your coverage stays at 42%.**

With smallsteps you declare your goal of 80% coverage and that you want to reach it in 100 days. Smallsteps computes the necessary percentage that must be met for each day (e.g. after 50 days you need 60% coverage) and fails if the goal is not met.

## Example

We are using this repository itself as an example. We want to enforce our test coverage to go up.
So we create a ratchet:

```
uvx smallsteps add \
  --name="Pytest Coverage" \
  --command="uv run pytest --cov --cov-report=json > /dev/null && jq -r '.totals.percent_covered' coverage.json" \
  --goal=80 \
  --end="2026-10-01"
```

This created a new file – `smallsteps.toml` – which holds the configuration of our ratchet:

```toml
# Smallsteps Configuration

[[ratchets]]
name = "Pytest Coverage"
start = 2026-06-25
end = 2026-10-01
initial_value = 57.142857142857146
goal_value = 80
command = "uv run pytest --cov --cov-report=json > /dev/null 2>&1 && jq -r '.totals.percent_covered' coverage.json"

```

**Note**

- You don't need to memorize the command parameters, `smallsteps add` walks you through them interactively.
- Ratchets can be increasing or decreasing. Percentages (56% with explicit "%") are parsed as floats (.56). So make sure that your goal format matches the command output: if the output is plain 56, the goal should also be 56. If its 56%, the goal must be 56% or .56.
- It's allways a good idea to mute your original commands output (using `> /dev/null 2>&1`) and write the value into a file to make the result parsing easier.

You can inspect, add or modify the ratchets using the toml file. There will find also another example using basedpyright.

### Checking your Ratchets

Run `uvx smallsteps check` to check the status of your ratchets. To simulate the future you can run with `--date`, e.g.:

```
uv smallsteps check --date 2026-10-31
Evaluating 1 ratchet(s)...

Pytest Coverage: BEHIND (Current: 57.14, Expected Min: 80.00)

Progress check failed.

```

shows that on the goal date the check will fail if we do not achieve 80% test coverage.

### CI and reading values from env

By default, running smallsteps check executes the underlying shell commands to gather active metrics. In modern CI/CD, you may prefer to compute metrics once during separate pipeline steps rather than using Smallsteps as a heavy task orchestrator.

By default smallsteps looks for environment variables matching the ratchets before running the command. E.g. if `SMALLSTEPS_PYTEST_COVERAGE` is present, the coverage is not re-computed. You can use this in CI to pass outputs from test workflow into the smallsteps action. To get a scaffolding github action with the required input vars for your ratchets run `uvx smallsteps ci`.

Have a look at [the action](.github/actions/smallsteps/action.yaml) and the whole workflow (not provided by a command because too specific for your setup) to see how the plumbing can work.

## Installation

This documentation assumes you are using `uv`, hence you don't need to do anything despite using the uv tool command (`uvx`) to install and run smallsteps.

# License

MIT
