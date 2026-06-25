# Smallsteps - improve your codebase in small steps

Smallsteps allows you to declare ratchets – metrics that must improve over time – and to enforce them via local testing or CI pipelines.

A typical situation: you want to add test coverage as a health check.
Initially your coverage is at 42% so you create a CI gate that fails if it falls under 40%. Now you have your baseline secured – so far so good. You make a resolution to yourself: you will increase your coverage and bump up the minimum percentage frequently.
**Somehow, that never happens, and your coverage stays at 42%.**

With smallsteps you declare your goal of 80% coverage and that you want to reach it in 100 days. Smallsteps computes the exact target value required for the current day (e.g., after 50 days, you need at least 60% coverage) and fails the build if your codebase falls behind the trend line.

## Example

We use this repository itself as an example to enforce our test coverage tracking.
To create a new coverage ratchet, run:

```
uvx smallsteps add \
  --name="Pytest Coverage" \
  --command="uv run pytest --cov --cov-report=json > /dev/null && jq -r '.totals.percent_covered' coverage.json" \
  --goal=80 \
  --end="2026-10-01"
```

This automatically initializes a smallsteps.toml file in your project root to hold your configuration:

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

- You don't need to memorize CLI parameters as `smallsteps add` walks you through them interactively.
- Ratchets can be increasing or decreasing
- Ensure your `--goal` representation matches your command's output format (e.g., if your tool outputs `85%`, use a goal of `100%`; if it outputs raw floats like `85.0`, match it with `100`).
- It's allways a good idea to mute commands outputs (using `> /dev/null 2>&1`) to make the result parsing easier.

You can inspect, add or modify the ratchets using the config file. In it you can also find another example using basedpyright.

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

Running smallsteps executes the underlying shell commands to evaluate the ratchet health. In CI/CD, you may prefer to compute metrics once during separate pipeline steps rather than using smallsteps as a task orchestrator.

To accommodate this, smallsteps searches the shell environment for matching `SMALLSTEPS_` variables before running any command. E.g. if `SMALLSTEPS_PYTEST_COVERAGE` is present, the coverage is not re-computed. You can use this in CI to pass outputs from a another workflow into the smallsteps action. To bootstrap a github action containing the required input vars mapped to your ratchets run `uvx smallsteps ci`.

Have a look at [the smallsteps action](.github/actions/smallsteps/action.yaml) and the whole [workflow](.github/workflows/ci.yaml) (not created by a command because too specific for your setup) to see an example of the wiring.

## Installation

This documentation assumes you are using `uv`, hence you don't need follow any manual steps and can run smallsteps on the fly using th uv tool command (`uvx`). All other ways of managing python dependencies will work as well.

# License

MIT

# Inspiration

["It gets easier. Every day it gets a little easier. But you got to do it every day. That's the hard part. But it does get easier."](https://www.youtube.com/watch?v=R2_Mn-qRKjA)
