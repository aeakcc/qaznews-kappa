"""Agreement measures and the batch report.

Annotations come in long format: one row per (item, annotator, label).
Cohen's kappa is computed for every pair of annotators on the items both labelled;
their mean is Light's kappa, the headline value. Fleiss' kappa uses the items
labelled by every annotator.
"""

import csv
from collections import Counter, defaultdict
from itertools import combinations

COLUMNS = ("item", "annotator", "label")

# Landis and Koch (1977) verbal scale
BANDS = [
    (0.8, "almost perfect"),
    (0.6, "substantial"),
    (0.4, "moderate"),
    (0.2, "fair"),
    (0.0, "slight"),
]


def load(path):
    """Read a CSV with columns item, annotator, label into {item: {annotator: label}}."""
    data = defaultdict(dict)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = set(COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing column(s): {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            item, annotator, label = ((row[c] or "").strip() for c in COLUMNS)
            if not (item and annotator and label):
                raise ValueError(f"line {line}: empty item, annotator or label")
            if data[item].get(annotator, label) != label:
                raise ValueError(f"line {line}: {annotator} gave item {item} two different labels")
            data[item][annotator] = label
    if not data:
        raise ValueError("no annotations")
    return dict(data)


def cohen_kappa(a, b):
    """Cohen's kappa of two equal-length label sequences; None if chance agreement is 1."""
    if not a or len(a) != len(b):
        raise ValueError("need two non-empty label sequences of equal length")
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in ca) / n**2
    return None if pe == 1 else (po - pe) / (1 - pe)


def fleiss_kappa(rows):
    """Fleiss' kappa; rows[i] holds the labels of item i, every item has the same number m >= 2."""
    m = len(rows[0]) if rows else 0
    if m < 2 or any(len(r) != m for r in rows):
        raise ValueError("every item needs the same number (at least 2) of labels")
    n = len(rows)
    p_bar = sum(c * (c - 1) for r in rows for c in Counter(r).values()) / (n * m * (m - 1))
    pe = sum((t / (n * m)) ** 2 for t in Counter(x for r in rows for x in r).values())
    return None if pe == 1 else (p_bar - pe) / (1 - pe)


def band(kappa):
    if kappa is None:
        return "undefined"
    return next((name for floor, name in BANDS if kappa >= floor), "poor")


def report(data):
    """Agreement figures for one batch, as plain data (JSON-serialisable)."""
    annotators = sorted({a for labels in data.values() for a in labels})
    if len(annotators) < 2:
        raise ValueError("need labels from at least two annotators")
    pairs, confusions = [], Counter()
    for x, y in combinations(annotators, 2):
        both = [labels for labels in data.values() if x in labels and y in labels]
        if not both:
            continue
        a, b = [lab[x] for lab in both], [lab[y] for lab in both]
        observed = sum(p == q for p, q in zip(a, b, strict=True)) / len(both)
        pairs.append(dict(pair=[x, y], items=len(both), observed=observed, kappa=cohen_kappa(a, b)))
        confusions.update(tuple(sorted(p)) for p in zip(a, b, strict=True) if p[0] != p[1])
    defined = [p["kappa"] for p in pairs if p["kappa"] is not None]
    light = sum(defined) / len(defined) if defined else None
    k = len(annotators)
    complete = [[lab[a] for a in annotators] for lab in data.values() if len(lab) == k]
    return dict(
        items=len(data),
        annotators=annotators,
        labels=sorted({x for lab in data.values() for x in lab.values()}),
        pairs=pairs,
        kappa=light,
        band=band(light),
        fleiss=fleiss_kappa(complete) if complete else None,
        complete_items=len(complete),
        confusions=[[a, b, n] for (a, b), n in confusions.most_common(5)],
    )
