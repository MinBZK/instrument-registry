"""De relaties tussen vragen in de instrumenten, als graaf.

Een vraag kan via `references` verwijzen naar een vraag in een ander instrument
(of hetzelfde), om een antwoord te tonen (pre-view) of over te nemen (pre-fill,
one-to-one, ...). Met veel instrumenten ontstaan daaruit ketens: A neemt over
van B, dat weer toont uit C. Een cirkel in zo'n keten heeft geen begin, en een
lange keten maakt onnavolgbaar waar een antwoord vandaan komt.

De sleutel van een verwijzing is de naam van het doelinstrument (`DPIA`,
`IAMA`); urn.for_name vertaalt die naar een URN. Hoort de sleutel bij een
instrument, dan telt elke vorm mee: `"1.1"`, `["1.1"]` of `{id, type}`. Hoort hij
nergens bij, dan wijst een kale string (zoals `prescanModelId: "3"`) buiten de
registry; een `{id, type}` wijst dan naar een onbekend instrument.
"""

from collections.abc import Iterator
from typing import Any, cast

from instrument_registry import urn

# Een vraag in de registry: (bestandsnaam van het instrument, vraag-id).
Node = tuple[str, str]
Graph = dict[Node, list[Node]]


def _tasks(tasks: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for task in tasks:
        yield task
        yield from _tasks(task.get("tasks", []))


def _question_ids(value: Any, include_strings: bool) -> list[str]:
    """Return the question ids in one reference value; plain strings only when asked."""
    items = cast(list[Any], value) if isinstance(value, list) else [value]
    ids: list[str] = []
    for item in items:
        if isinstance(item, dict) and "id" in item:
            ids.append(str(cast(dict[str, Any], item)["id"]))
        elif include_strings and isinstance(item, str | int | float):
            ids.append(str(item))
    return ids


def build_graph(documents: dict[str, dict[str, Any]]) -> tuple[Graph, list[tuple[Node, str]]]:
    """Collect every question-to-question reference.

    Returns the graph and the references whose target does not exist, each as
    the referring question and a readable description of the missing target.
    """
    urns = {
        file_name: document["urn"] for file_name, document in documents.items() if isinstance(document.get("urn"), str)
    }
    question_ids = {
        file_name: {str(task["id"]) for task in _tasks(document.get("tasks", [])) if "id" in task}
        for file_name, document in documents.items()
    }
    graph: Graph = {}
    unresolved: list[tuple[Node, str]] = []
    for file_name, document in documents.items():
        for task in _tasks(document.get("tasks", [])):
            references: dict[str, Any] = task.get("references") or {}
            if "id" not in task:
                continue
            source: Node = (file_name, str(task["id"]))
            for key, value in references.items():
                target_file = urn.resolve(urn.for_name(key), urns)
                for target_id in _question_ids(value, include_strings=target_file is not None):
                    if target_file is None:
                        unresolved.append((source, f"{key} {target_id} (unknown instrument {key})"))
                    elif target_id not in question_ids[target_file]:
                        unresolved.append((source, f"{key} {target_id} (unknown question)"))
                    else:
                        graph.setdefault(source, []).append((target_file, target_id))
    return graph, unresolved


def find_cycles(graph: Graph) -> list[list[Node]]:
    """Return the cycles a depth-first walk runs into, each set of questions once.

    Each cycle starts and ends with the same question. The walk is iterative,
    so long chains do not hit Python's recursion limit.
    """
    on_path, done = 1, 2
    state: dict[Node, int] = {}
    cycles: list[list[Node]] = []
    seen: set[frozenset[Node]] = set()
    for start in graph:
        if start in state:
            continue
        path = [start]
        children = [iter(graph.get(start, []))]
        state[start] = on_path
        while children:
            child = next(children[-1], None)
            if child is None:
                state[path.pop()] = done
                children.pop()
            elif state.get(child) == on_path:
                cycle = path[path.index(child) :] + [child]
                if frozenset(cycle) not in seen:
                    seen.add(frozenset(cycle))
                    cycles.append(cycle)
            elif child not in state:
                state[child] = on_path
                path.append(child)
                children.append(iter(graph.get(child, [])))
    return cycles


def longest_chains(graph: Graph) -> list[list[Node]]:
    """Return, per question nothing refers to, the longest chain that starts there.

    Only defined for a graph without cycles; check with find_cycles first.
    """
    longest: dict[Node, list[Node]] = {}
    for start in graph:
        stack = [start]
        while stack:
            node = stack[-1]
            if node in longest:
                stack.pop()
                continue
            pending = [child for child in graph.get(node, []) if child not in longest]
            if pending:
                stack.extend(pending)
                continue
            no_chain: list[Node] = []
            longest[node] = [node, *max((longest[child] for child in graph.get(node, [])), key=len, default=no_chain)]
            stack.pop()
    targets = {child for children in graph.values() for child in children}
    return [longest[node] for node in graph if node not in targets]
