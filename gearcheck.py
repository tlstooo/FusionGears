"""Consistency of a gear train built from motion links. No Fusion dependencies.

Each joint is a node; each motion link is an edge (a, b, k, name) meaning
"turning a by 1 turns b by k" in the joints' own frames. A train is consistent
when every joint gets a single speed whichever chain of links drives it; a
loop with an odd number of external meshes (three gears in a triangle) or with
a ratio product other than 1 is reported, with the chains that disagree.
"""
from collections import deque

REL_TOL = 1e-6


def find_conflicts(links):
    """Return a list of conflicts: dicts with joint, both speeds and both chains."""
    adj = {}
    for i, (a, b, k, name) in enumerate(links):
        adj.setdefault(a, []).append((b, k, name, i))
        adj.setdefault(b, []).append((a, 1.0 / k, name, i))

    speed, chain, conflicts, used = {}, {}, [], set()
    for start in adj:
        if start in speed:
            continue
        speed[start], chain[start] = 1.0, []
        queue = deque([start])
        while queue:
            a = queue.popleft()
            for b, k, name, i in adj[a]:
                if i in used:
                    continue
                used.add(i)
                w = speed[a] * k
                path = chain[a] + [name]
                if b not in speed:
                    speed[b], chain[b] = w, path
                    queue.append(b)
                elif abs(speed[b] - w) > REL_TOL * max(abs(w), abs(speed[b])):
                    conflicts.append({'joint': b, 'speed': speed[b], 'other_speed': w,
                                      'chain': chain[b], 'other_chain': path,
                                      'opposite': (speed[b] > 0) != (w > 0)})
    return conflicts


def describe(conflict, label=str):
    """Russian one-line description of a conflict."""
    kind = 'в разные стороны' if conflict['opposite'] else 'с разной скоростью'
    first = ' → '.join(conflict['chain']) or 'ведущее соединение'
    second = ' → '.join(conflict['other_chain'])
    return (f'{label(conflict["joint"])}: связи заставляют вращаться {kind} '
            f'(через {first}: {conflict["speed"]:+.4g}; через {second}: {conflict["other_speed"]:+.4g})')
