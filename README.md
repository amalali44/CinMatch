# Personalized Recommendation & Analytics Pipeline

A MovieLens recommendation project built incrementally with Python, SQL,
PySpark, scikit-learn, and Docker.

**Current stage: project foundation.** This repository provides an installable
Python package, streaming CSV validation, a data profile command, synthetic
sample data, and CI. ETL, models, evaluation, and containers are planned work.
No full MovieLens 25M run or recommendation performance is claimed yet.

## Quick start

Requires Python 3.11+. Runtime code uses only the standard library.

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
recsys profile --sample --output artifacts/sample-profile.json
python -m unittest discover -s tests -v
```

You can also use `python -m recsys profile --sample` after installation.
The bundled fixture contains 12 **synthetic** interactions, for smoke testing.

## Profile real data

Download and extract MovieLens separately, then supply its ratings file:

```sh
recsys profile --ratings data/raw/ml-25m/ratings.csv --output artifacts/ml25m-profile.json
```

The command validates `userId`, `movieId`, `rating`, and `timestamp`, then emits
JSON containing interaction count, rating statistics, and timestamp range.
Processing uses constant working memory, one CSV row at a time. Invalid rows
produce an error with a line number and exit code 2. Extra named columns are
accepted. Deduplication and metadata joins belong to the upcoming ETL stage.

MovieLens 25M contains 25 million ratings. See the official
[dataset page](https://grouplens.org/datasets/movielens/25m/) and the README and
usage terms included in its download. Data and generated artifacts stay out of Git.

## Structure

```text
src/recsys/       CLI, data contract, and synthetic fixture
tests/           Data-contract and command tests
docs/roadmap.md   Implementation stages and acceptance checks
data/raw/        Local downloads (ignored)
artifacts/       Generated profiles and future models (ignored)
```

## Planned pipeline

```text
MovieLens CSV → PySpark + SQL ETL → partitioned Parquet
             → temporal splits → collaborative filtering
             → Precision@K, Recall@K, RMSE → model artifacts + inference
```

Spark ALS will provide distributed collaborative filtering; scikit-learn will
provide a small-data baseline. See the [roadmap](docs/roadmap.md) for staged
implementation and evidence required before reporting full-scale results.
