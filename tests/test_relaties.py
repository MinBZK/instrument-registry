from typing import Any

from instrument_registry import relaties, validate


def instrument(urn: str, *tasks: dict[str, Any]) -> dict[str, Any]:
    return {"urn": urn, "tasks": list(tasks)}


def task(task_id: str, **references: Any) -> dict[str, Any]:
    return {"id": task_id, "references": references} if references else {"id": task_id}


def pre_view(task_id: str) -> list[dict[str, str]]:
    return [{"id": task_id, "type": "pre-view"}]


def test_references_between_instruments_become_edges() -> None:
    documents = {
        "prescan.yaml": instrument("urn:nl:prescan", task("1", DPIA=pre_view("2"), prescanModelId="7")),
        "dpia.yaml": instrument("urn:nl:dpia", task("2")),
    }

    graph, unresolved = relaties.build_graph(documents)

    assert graph == {("prescan.yaml", "1"): [("dpia.yaml", "2")]}
    assert unresolved == []


def test_nested_tasks_and_single_object_references_are_found() -> None:
    documents = {
        "dpia.yaml": instrument(
            "urn:nl:dpia",
            {"id": "1", "tasks": [task("1.1", DPIA={"id": "2", "type": "direct takeover"})]},
            task("2"),
        ),
    }

    graph, _ = relaties.build_graph(documents)

    assert graph == {("dpia.yaml", "1.1"): [("dpia.yaml", "2")]}


def test_references_to_missing_instruments_and_questions_are_unresolved() -> None:
    documents = {
        "dpia.yaml": instrument("urn:nl:dpia", task("1", KIA=pre_view("3"), DPIA=pre_view("99"))),
    }

    _, unresolved = relaties.build_graph(documents)

    assert unresolved == [
        (("dpia.yaml", "1"), "KIA 3 (unknown instrument KIA)"),
        (("dpia.yaml", "1"), "DPIA 99 (unknown question)"),
    ]


def test_a_cycle_is_found_once() -> None:
    graph: relaties.Graph = {("a", "1"): [("a", "2")], ("a", "2"): [("a", "3")], ("a", "3"): [("a", "1")]}

    assert relaties.find_cycles(graph) == [[("a", "1"), ("a", "2"), ("a", "3"), ("a", "1")]]


def test_a_question_referring_to_itself_is_a_cycle() -> None:
    assert relaties.find_cycles({("a", "1"): [("a", "1")]}) == [[("a", "1"), ("a", "1")]]


def test_shared_targets_are_not_a_cycle() -> None:
    graph: relaties.Graph = {("a", "1"): [("a", "3")], ("a", "2"): [("a", "3")]}

    assert relaties.find_cycles(graph) == []


def test_longest_chain_is_reported_per_starting_question() -> None:
    graph: relaties.Graph = {
        ("a", "1"): [("a", "2"), ("a", "9")],
        ("a", "2"): [("a", "3")],
        ("a", "8"): [("a", "9")],
    }

    assert relaties.longest_chains(graph) == [
        [("a", "1"), ("a", "2"), ("a", "3")],
        [("a", "8"), ("a", "9")],
    ]


def test_long_chains_do_not_hit_the_recursion_limit() -> None:
    graph: relaties.Graph = {("a", str(i)): [("a", str(i + 1))] for i in range(5000)}

    assert relaties.find_cycles(graph) == []
    assert len(relaties.longest_chains(graph)[0]) == 5001


def chain_documents(length: int) -> dict[str, dict[str, Any]]:
    tasks = [task(str(i), DPIA=pre_view(str(i + 1))) for i in range(length)] + [task(str(length))]
    return {"dpia.yaml": instrument("urn:nl:dpia", *tasks)}


def test_chain_within_the_limit_passes() -> None:
    assert validate.check_relations(chain_documents(3), max_chain_length=3) == []


def test_chain_over_the_limit_is_reported() -> None:
    errors = validate.check_relations(chain_documents(4), max_chain_length=3)

    assert [error.message for error in errors] == [
        "chain of 4 references exceeds 3: dpia.yaml#0 -> dpia.yaml#1 -> dpia.yaml#2 -> dpia.yaml#3 -> dpia.yaml#4"
    ]


def test_cycle_is_reported_across_instruments() -> None:
    documents = {
        "dpia.yaml": instrument("urn:nl:dpia", task("1", IAMA=pre_view("2"))),
        "iama.yaml": instrument("urn:nl:iama", task("2", DPIA=[{"id": "1", "type": "pre-fill"}])),
    }

    errors = validate.check_relations(documents)

    assert [(error.file, error.message) for error in errors] == [
        ("dpia.yaml", "references form a cycle: dpia.yaml#1 -> iama.yaml#2 -> dpia.yaml#1")
    ]


def test_unresolved_reference_is_reported() -> None:
    documents = {"dpia.yaml": instrument("urn:nl:dpia", task("1", DPIA=pre_view("99")))}

    errors = validate.check_relations(documents)

    assert [error.message for error in errors] == ["question 1 refers to DPIA 99 (unknown question)"]
