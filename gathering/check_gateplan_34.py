"""Independent minute-grid feasibility oracle for bounded gate schedules."""
import itertools
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path('line-1/tools/gateplan').resolve()))
import gateplan


def oracle(rows, gates, workers, deadline):
    durations = {row['id']: row['minutes'] for row in rows}
    needs = {row['id']: set(row.get('after', [])) for row in rows}
    deadlines = {name: deadline for name in durations}
    for gate in gates:
        for name in gate['tasks']:
            deadlines[name] = min(deadlines[name], gate['due'])
    states = {(frozenset(), ())}
    for minute in range(deadline + 1):
        if any(len(done) == len(rows) for done, _ in states):
            return minute
        next_states = set()
        for done, active in states:
            busy = dict(active)
            ready = [name for name in durations if name not in done
                     and name not in busy and needs[name] <= done]
            for count in range(min(workers - len(busy), len(ready)) + 1):
                for chosen in itertools.combinations(ready, count):
                    running = dict(busy)
                    running.update((name, durations[name]) for name in chosen)
                    completed = {name for name, left in running.items() if left == 1}
                    if any(minute + 1 > deadlines[name] for name in completed):
                        continue
                    remaining = tuple(sorted((name, left - 1)
                                             for name, left in running.items() if left > 1))
                    next_states.add((done | completed, remaining))
        states = next_states
    return None


rng = random.Random(7373401)
feasible = infeasible = 0
for case in range(180):
    count = rng.randint(1, 5)
    rows = [{'id': str(i), 'minutes': rng.randint(1, 3),
             'after': [str(j) for j in range(i) if rng.random() < .3]}
            for i in range(count)]
    deadline = rng.randint(1, sum(row['minutes'] for row in rows) + 2)
    gates = [{'id': 'gate-' + str(i),
              'tasks': rng.sample([row['id'] for row in rows], rng.randint(1, count)),
              'due': rng.randint(0, deadline + 2)} for i in range(rng.randint(1, 3))]
    workers = rng.randint(1, 3)
    expected = oracle(rows, gates, workers, deadline)
    report = gateplan.solve({'tasks': rows}, {'gates': gates}, workers, deadline)
    if expected is None:
        assert report['status'] == 'infeasible', (case, report)
        infeasible += 1
    else:
        assert report['status'] == 'feasible', (case, report)
        assert report['plan']['finish'] == expected, (case, expected, report)
        feasible += 1
print(json.dumps({'passed': True, 'seed': 7373401, 'cases': feasible + infeasible,
                  'feasible': feasible, 'infeasible': infeasible,
                  'oracle': 'all available start subsets at every integer minute',
                  'tool': 'event-search Gateplan', 'maximum_tasks': 5}))
