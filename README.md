# qaznews-kappa

[![CI](https://github.com/aeakcc/qaznews-kappa/actions/workflows/ci.yml/badge.svg)](https://github.com/aeakcc/qaznews-kappa/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small command-line tool that measures inter-annotator agreement on a batch of labelled
texts and fails when the agreement is too low. It reports Cohen's kappa for every pair of
annotators, their mean (Light's kappa), Fleiss' kappa and the label pairs that annotators
confuse most often.

## Why

The tool belongs to **QazNews Insight**, a research project on topic classification, named
entity recognition and sentiment analysis of Kazakh- and Russian-language news. The training
corpus (about 12,000 articles) is labelled by several annotators in batches. A batch is
accepted only if annotators agree well enough; otherwise the annotation guidelines are revised
and the batch is relabelled. `qaznews-kappa` is that check: it runs on each new batch, and
its exit code can stop a pipeline.

## Install

Python 3.10 or newer; no third-party packages are needed at run time.

```bash
pip install git+https://github.com/aeakcc/qaznews-kappa
```

A wheel of every tagged version is attached to its
[GitHub release](https://github.com/aeakcc/qaznews-kappa/releases).

## Usage

Input is a CSV file in long format, one row per label. Items may be labelled by any subset of
annotators.

```csv
item,annotator,label
qn-ok-001,ann1,politics
qn-ok-001,ann2,politics
qn-ok-001,ann3,economy
```

```console
$ qaznews-kappa examples/batch_ok.csv --min-kappa 0.7
batch       examples/batch_ok.csv
items       60 (58 labelled by all annotators)
annotators  ann1, ann2, ann3
labels      culture, economy, incidents, politics, society, sport

pair                   items  observed   kappa
ann1 ~ ann2               60     0.867   0.833
ann1 ~ ann3               58     0.879   0.850
ann2 ~ ann3               58     0.776   0.721

Light's kappa (mean pairwise Cohen)  0.801  almost perfect
Fleiss' kappa                        0.799
most frequent disagreements: incidents / society (8), culture / sport (6), economy / politics (6), culture / society (4), economy / incidents (2)
gate        kappa 0.801 vs minimum 0.700: PASS
```

| Option | Meaning |
|---|---|
| `--min-kappa K` | exit with code 1 if Light's kappa is below `K` |
| `--json` | print the report as JSON (for scripts and dashboards) |
| `--version` | print the version |

Exit codes: `0` the batch passes, `1` agreement is below the minimum, `2` the input is invalid
(missing column, empty cell, the same annotator giving one item two labels).

The same functions are available from Python:

```python
from qaznews_kappa import cohen_kappa, fleiss_kappa, load, report

r = report(load("examples/batch_ok.csv"))
print(r["kappa"], r["fleiss"])
```

## Measures

For two annotators with observed agreement $p_o$ and chance agreement $p_e$ (from each
annotator's own label frequencies), **Cohen's kappa** is

$$\kappa = \frac{p_o - p_e}{1 - p_e}.$$

With more than two annotators the tool computes Cohen's kappa for every pair on the items both
of them labelled and reports the mean, **Light's kappa**, as the headline value. **Fleiss'
kappa** is reported as well; it uses only the items labelled by every annotator. When chance
agreement equals 1 (everyone used a single label) kappa is undefined and is shown as `n/a`.

The verbal scale follows Landis and Koch (1977): below 0 poor, 0 to 0.2 slight, 0.2 to 0.4
fair, 0.4 to 0.6 moderate, 0.6 to 0.8 substantial, 0.8 and above almost perfect. QazNews uses
0.7 as the acceptance threshold for a batch.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest                     # unit tests
ruff check . && ruff format --check .
```

The tests check the formulas against published worked examples. A further test compares the
results with scikit-learn and statsmodels on 200 random batches; it runs when those packages
are installed (`pip install scikit-learn statsmodels`) and always runs in CI.

`examples/generate.py` regenerates the two synthetic example batches from a fixed seed.

### Continuous integration and delivery

- [`ci.yml`](.github/workflows/ci.yml) runs on every push to `main` and every pull request:
  lint and format check (ruff), tests with coverage on Python 3.10 to 3.14 (Ubuntu) and on
  Windows and macOS, the cross-check against reference libraries, the agreement gate on the
  example batch, and a build of the wheel and sdist, which are kept as a workflow artifact.
- [`release.yml`](.github/workflows/release.yml) runs when a tag `v*` is pushed. It checks
  that the tag matches the package version, tests, builds and publishes a GitHub release
  with the files attached.

To release: raise `__version__` in `src/qaznews_kappa/__init__.py`, merge, then
`git tag v0.2.0 && git push origin v0.2.0`.

## Citation

If you use the tool in research, please cite it with the metadata in
[`CITATION.cff`](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
