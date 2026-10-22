"""De relaties tussen vragen in de instrumenten, als graaf.

Een vraag kan via `references` verwijzen naar een vraag in een ander instrument
(of hetzelfde), om een antwoord te tonen (pre-view) of over te nemen (pre-fill,
one-to-one, ...). Met veel instrumenten ontstaan daaruit ketens: A neemt over
van B, dat weer toont uit C. Een cirkel in zo'n keten heeft geen begin, en een
lange keten maakt onnavolgbaar waar een antwoord vandaan komt.

De sleutel van een verwijzing is de naam van het doelinstrument (`DPIA`,
`IAMA`) en hoort bij de URN `urn:nl:<naam in kleine letters>`. Verwijzingen
zonder vraag-id, zoals `prescanModelId`, wijzen buiten de registry en tellen
hier niet mee.
"""

from collections.abc import Iterator
from typing import Any, cast

# Een vraag in de registry: (bestandsnaam van het instrument, vraag-id).
Node = tuple[str, str]
Graph = dict[Node, list[Node]]


def _tasks(tasks: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for task in tasks:
        yield task
        yield from _tasks(task.get("tasks", []))


def _task_references(value: Any) -> list[str]:
    """Return the question ids in one reference value, skipping plain external ids."""
    items = cast(list[Any], value) if isinstance(value, list) else [value]
    references = [cast(dict[str, Any], item) for item in items if isinstance(item, dict)]
    return [str(reference["id"]) for reference in references if "id" in reference]


def build_graph(documents: dict[str, dict[str, Any]]) -> tuple[Graph, list[tuple[Node, str]]]:
    """Collect every question-to-question reference.

    Returns the graph and the references whose target does not exist, each as
    the referring question and a readable description of the missing target.
    """
    files_by_urn = {
        document["urn"]: file_name for file_name, document in documents.items() if isinstance(document.get("urn"), str)
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
            source: Node = (file_name, str(task.get("id")))
            for key, value in references.items():
                target_ids = _task_references(value)
                if not target_ids:
                    continue
                target_file = files_by_urn.get(f"urn:nl:{key.lower()}")
                for target_id in target_ids:
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
