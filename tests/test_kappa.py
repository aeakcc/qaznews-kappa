import json
import random

import pytest

from qaznews_kappa import cohen_kappa, fleiss_kappa, load, report
from qaznews_kappa.cli import main

# Worked example of the Wikipedia article "Fleiss' kappa": 10 items, 14 raters, 5 categories,
# counts of raters per category. Published result: kappa = 0.210.
FLEISS_TABLE = [
    (0, 0, 0, 0, 14),
    (0, 2, 6, 4, 2),
    (0, 0, 3, 5, 6),
    (0, 3, 9, 2, 0),
    (2, 2, 8, 1, 1),
    (7, 7, 0, 0, 0),
    (3, 2, 6, 3, 0),
    (2, 5, 3, 2, 2),
    (6, 5, 2, 1, 0),
    (0, 2, 2, 3, 7),
]


def write(tmp_path, text, name="batch.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_cohen_textbook_example():
    # Wikipedia "Cohen's kappa": 50 items, 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no -> 0.4
    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    assert cohen_kappa(a, b) == pytest.approx(0.4)
    assert cohen_kappa(b, a) == pytest.approx(0.4)


def test_cohen_limits():
    assert cohen_kappa("abab", "abab") == 1
    assert cohen_kappa("abab", "baba") == pytest.approx(-1)
    assert cohen_kappa("aaaa", "aaaa") is None  # chance agreement is 1: undefined
    with pytest.raises(ValueError):
        cohen_kappa("ab", "a")


def test_fleiss_textbook_example():
    rows = [[cat for cat, n in enumerate(counts) for _ in range(n)] for counts in FLEISS_TABLE]
    assert round(fleiss_kappa(rows), 3) == 0.210


def test_fleiss_rejects_ragged_rows():
    with pytest.raises(ValueError):
        fleiss_kappa([["a", "b"], ["a"]])
    with pytest.raises(ValueError):
        fleiss_kappa([["a"], ["b"]])


def test_load(tmp_path):
    path = write(tmp_path, "﻿item,annotator,label\n1,ann1,sport\n1,ann1,sport\n1,ann2, sport \n")
    assert load(path) == {"1": {"ann1": "sport", "ann2": "sport"}}


@pytest.mark.parametrize(
    "text, message",
    [
        ("item,label\n1,sport\n", "missing column"),
        ("item,annotator,label\n1,ann1,sport\n1,ann1,culture\n", "two different labels"),
        ("item,annotator,label\n1,ann1,\n", "empty"),
        ("item,annotator,label\n", "no annotations"),
    ],
)
def test_load_rejects_bad_input(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load(write(tmp_path, text))


def test_report_with_missing_label():
    data = {
        "1": {"a": "x", "b": "x", "c": "x"},
        "2": {"a": "y", "b": "y", "c": "x"},
        "3": {"a": "x", "b": "y"},  # c skipped this item
        "4": {"a": "y", "b": "y", "c": "y"},
    }
    r = report(data)
    assert r["items"] == 4 and r["complete_items"] == 3
    assert [p["items"] for p in r["pairs"]] == [4, 3, 3]
    assert r["kappa"] == pytest.approx(sum(p["kappa"] for p in r["pairs"]) / 3)
    assert r["confusions"][0] == ["x", "y", 3]


def test_report_needs_two_annotators():
    with pytest.raises(ValueError):
        report({"1": {"a": "x"}, "2": {"a": "y"}})


BATCH = "item,annotator,label\n" + "".join(
    f"{i},ann1,{x}\n{i},ann2,{y}\n" for i, (x, y) in enumerate(["aa", "bb", "aa", "bb", "ab"])
)


def test_cli_text_and_gate(tmp_path, capsys):
    path = write(tmp_path, BATCH)  # kappa = 0.615
    assert main([str(path)]) == 0
    assert "Light's kappa" in capsys.readouterr().out
    assert main([str(path), "--min-kappa", "0.6"]) == 0
    assert main([str(path), "--min-kappa", "0.7"]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_cli_json(tmp_path, capsys):
    assert main([str(write(tmp_path, BATCH)), "--json", "--min-kappa", "0.7"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["passed"] is False and out["kappa"] == pytest.approx(0.6154, abs=1e-4)


def test_cli_bad_input(tmp_path, capsys):
    assert main([str(tmp_path / "missing.csv")]) == 2
    assert main([str(write(tmp_path, "id,label\n"))]) == 2
    assert "missing column" in capsys.readouterr().err


def test_matches_reference_implementations():
    """Random batches against scikit-learn and statsmodels (runs only where they are installed)."""
    metrics = pytest.importorskip("sklearn.metrics")
    inter_rater = pytest.importorskip("statsmodels.stats.inter_rater")
    rng = random.Random(1)
    for _ in range(200):
        n, m, k = rng.randint(5, 80), rng.randint(2, 6), rng.randint(2, 6)
        rows = [[rng.randrange(k) for _ in range(m)] for _ in range(n)]
        a, b = [r[0] for r in rows], [r[1] for r in rows]
        if (ours := cohen_kappa(a, b)) is not None:
            assert ours == pytest.approx(metrics.cohen_kappa_score(a, b), abs=1e-12)
        if (ours := fleiss_kappa(rows)) is not None:
            table, _ = inter_rater.aggregate_raters(rows)
            assert ours == pytest.approx(inter_rater.fleiss_kappa(table), abs=1e-12)
