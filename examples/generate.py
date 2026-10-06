"""Regenerate the synthetic example batches: python examples/generate.py

Each annotator copies a hidden gold label with some accuracy; mistakes go mostly to a
neighbouring topic (politics/economy, society/incidents), as in real news annotation.
"""

import csv
import random
from pathlib import Path

LABELS = {"politics": 25, "economy": 20, "society": 20, "incidents": 15, "culture": 10, "sport": 10}
NEAR = {
    "politics": "economy",
    "economy": "politics",
    "society": "incidents",
    "incidents": "society",
    "culture": "society",
    "sport": "culture",
}


def annotate(rng, gold, accuracy):
    if rng.random() < accuracy:
        return gold
    if rng.random() < 0.7:
        return NEAR[gold]
    return rng.choice([x for x in LABELS if x != gold])


def batch(name, items, accuracy, skips=(), seed=2026):
    rng = random.Random(seed)
    gold = rng.choices(list(LABELS), weights=list(LABELS.values()), k=items)
    rows = [
        (f"qn-{name}-{i:03d}", f"ann{k + 1}", annotate(rng, g, acc))
        for i, g in enumerate(gold, 1)
        for k, acc in enumerate(accuracy)
        if (i, k + 1) not in skips
    ]
    path = Path(__file__).with_name(f"batch_{name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([("item", "annotator", "label"), *rows])


if __name__ == "__main__":
    batch("ok", 60, (0.93, 0.90, 0.88), skips={(17, 3), (42, 3)})
    batch("low", 40, (0.72, 0.62))
