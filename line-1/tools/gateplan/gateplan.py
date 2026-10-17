#!/usr/bin/env python3
"""Find a bounded exact schedule that meets intermediate task deadlines."""
import argparse
from functools import lru_cache
from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "plancheck"))
sys.path.insert(0, str(HERE.parent / "gatecheck"))
import plancheck  # noqa: E402
import gatecheck  # noqa: E402


def integer(value, label, ceiling=10000):
    number = value if isinstance(value, Fraction) else plancheck.number(value, label)
    if number.denominator != 1 or not 0 <= number <= ceiling:
        raise ValueError(f"{label} must be an integer from 0 to {ceiling}")
    return int(number)


def solve(tasks_data, gates_data, workers, budget, max_states=100000):
    """Return a shortest gated plan, or a proved infeasible result.

    Complete event search includes intentional idle capacity. Every feasible
    schedule can be left-shifted along its fixed worker order without making
    any task later, so at least one feasible optimum starts tasks at completion
    events. The state cap refuses to make a proof if search is cut short.
    """
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError("workers must be an integer from 1 to 4")
    if type(max_states) is not int or not 1 <= max_states <= 500000:
        raise ValueError("max_states must be an integer from 1 to 500000")
    deadline = integer(budget, "budget")
    graph = plancheck.graph(tasks_data)
    if len(graph) > 10:
        raise ValueError("gateplan is limited to 10 tasks")
    gates = gatecheck.validate_gates(gates_data, set(graph))
    names = sorted(graph)
    index = {name: i for i, name in enumerate(names)}
    durations = [integer(graph[name][0], "task minutes") for name in names]
    prerequisites = [sum(1 << index[dep] for dep in graph[name][1]) for name in names]
    due = [deadline] * len(names)
    for gate in gates:
        gate_due = integer(gate["due"], "gate due")
        for name in gate["tasks"]:
            due[index[name]] = min(due[index[name]], gate_due)
    all_done = (1 << len(names)) - 1
    examined = 0

    @lru_cache(maxsize=None)
    def search(done, active, now):
        nonlocal examined
        examined += 1
        if examined > max_states:
            raise ValueError("state limit exceeded; feasibility not established")
        if done == all_done:
            return now, ()
        busy = {task for task, _ in active}
        ready = tuple(i for i in range(len(names)) if
                      not (done >> i) & 1 and i not in busy and
                      prerequisites[i] & ~done == 0)
        capacity = min(workers - len(active), len(ready))
        choices = itertools.chain.from_iterable(
            itertools.combinations(ready, size)
            for size in range(0 if active else 1, capacity + 1))
        best = None
        for chosen in choices:
            running = tuple(sorted(active + tuple((i, durations[i]) for i in chosen)))
            if not running:
                continue
            step = min(remaining for _, remaining in running)
            next_time = now + step
            if next_time > deadline:
                continue
            next_done = done
            next_active = []
            missed = False
            for task, remaining in running:
                if remaining == step:
                    next_done |= 1 << task
                    missed |= next_time > due[task]
                else:
                    next_active.append((task, remaining - step))
            if missed:
                continue
            tail = search(next_done, tuple(next_active), next_time)
            if tail is not None:
                candidate = (tail[0], chosen)
                if best is None or candidate < best:
                    best = candidate
        return best

    optimum = search(0, (), 0)
    if optimum is None:
        return {"status": "infeasible", "proven": True,
                "workers": workers, "budget": deadline,
                "states_examined": examined, "state_limit": max_states}

    done, now = 0, 0
    active = []  # task, absolute finish, worker
    rows = []
    while done != all_done:
        state = tuple(sorted((task, finish - now) for task, finish, _ in active))
        _, chosen = search(done, state, now)
        occupied = {worker for _, _, worker in active}
        free = (worker for worker in range(1, workers + 1) if worker not in occupied)
        for task in chosen:
            worker = next(free)
            finish = now + durations[task]
            active.append((task, finish, worker))
            rows.append({"task": names[task], "worker": worker,
                         "start": now, "finish": finish})
        now = min(finish for _, finish, _ in active)
        for task, finish, _ in active:
            if finish == now:
                done |= 1 << task
        active = [item for item in active if item[1] != now]

    plan = {"units": "minutes", "workers": workers, "finish": now,
            "schedule": rows}
    if not plancheck.check(tasks_data, plan, workers, deadline)["valid"]:
        raise AssertionError("internal schedule failed Plancheck")
    if not gatecheck.check(tasks_data, plan, gates_data, workers, deadline)["valid"]:
        raise AssertionError("internal schedule failed Gatecheck")
    return {"status": "feasible", "proven": True,
            "objective": "shortest finish among schedules meeting all gates",
            "workers": workers, "budget": deadline,
            "states_examined": examined, "state_limit": max_states, "plan": plan}


def demo():
    # Shortest unconstrained order starts long background work first; the gate
    # instead needs the release task and its handoff finished by minute 3.
    tasks = {"tasks": [{"id": "release", "minutes": 1},
                       {"id": "handoff", "minutes": 2, "after": ["release"]},
                       {"id": "background", "minutes": 4}]}
    gates = {"gates": [{"id": "early", "tasks": ["handoff"], "due": 3}]}
    return tasks, gates


def self_test():
    tasks, gates = demo()
    result = solve(tasks, gates, 1, 7)
    assert result["status"] == "feasible" and result["plan"]["finish"] == 7
    assert result["plan"]["schedule"][0]["task"] == "release"
    assert solve(tasks, gates, 1, 6)["status"] == "infeasible"
    assert solve(tasks, gates, 2, 4)["plan"]["finish"] == 4
    assert solve(tasks, {"gates": [{"id": "early", "tasks": ["handoff"], "due": 2}]}, 2, 10)["status"] == "infeasible"
    tricky = {"tasks": [{"id": "prepare", "minutes": 1},
                         {"id": "a", "minutes": 7, "after": ["prepare"]},
                         {"id": "b", "minutes": 7, "after": ["prepare"]},
                         {"id": "join", "minutes": 8, "after": ["a", "b"]},
                         {"id": "background", "minutes": 6}]}
    open_gate = {"gates": [{"id": "join", "tasks": ["join"], "due": 16}]}
    assert solve(tricky, open_gate, 2, 16)["plan"]["finish"] == 16
    try:
        solve(tasks, gates, 1, 7, max_states=1)
    except ValueError as exc:
        assert "not established" in str(exc)
    else:
        raise AssertionError("state cap accepted a partial proof")
    return {"passed": True, "checks": 6}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--self-test", action="store_true")
    source.add_argument("--tasks")
    parser.add_argument("--gates")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--budget", type=int, default=10)
    parser.add_argument("--max-states", type=int, default=100000)
    args = parser.parse_args()
    try:
        if args.self_test:
            if args.gates is not None:
                raise ValueError("--self-test takes no gate file")
            result, code = self_test(), 0
        else:
            if args.demo:
                if args.gates is not None:
                    raise ValueError("--demo takes no gate file")
                tasks, gates = demo()
            else:
                if args.gates is None:
                    raise ValueError("--gates is required with --tasks")
                tasks = plancheck.read_json(args.tasks)
                gates = plancheck.read_json(args.gates)
            result = solve(tasks, gates, args.workers, args.budget, args.max_states)
            code = 0 if result["status"] == "feasible" else 2
        print(json.dumps(result, indent=2, allow_nan=False))
        return code
    except (ValueError, OSError, OverflowError, RecursionError) as exc:
        print("gateplan: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
