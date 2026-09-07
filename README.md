# AFL ML Prediction Model

Uses match, team and player data to identify pre-match indicators of winning, achieving over 75% accuracy on the held-out 2022 season.

Two models share one website:

- an AFL outcome and margin model; and
- a personalised, metadata-based book recommender.

Live site: [sam-speed-models.pages.dev](https://sam-speed-models.pages.dev/). See [CLOUDFLARE.md](CLOUDFLARE.md) for deployment and updates. AFL predictions are at `/afl`; book recommendations are at `/books`. Python/Flask is retained for training, local use, and parity tests.

## AFL model

- Historical window: 2012–2026, with 3,092 completed matches in the current snapshot.
- Untouched test season: 2022. Model selection and calibration use only data available before 2022; the production estimator excludes all 2022 match rows.
- Estimator: a calibrated blend of regularised linear regression and histogram gradient boosting.
- Inputs: opponent-adjusted results strength, rolling attack/defence, xScore, inside 50s, clearances, contested ball, scoring shots, player ratings, recent-lineup strength and continuity, rest, venue familiarity, and travel.
- Leakage protection: every match feature is a lagged or rolling value known before the bounce. Matches in the same round are calculated from the same pre-round state.
- Current 2022 holdout result: 75.2% tip accuracy and 25.34-point margin MAE across 207 matches.

The full reproducible evaluation and feature-importance output is stored in `app/artifacts/model_report.json`. Same-match correlations in that report are descriptive only; they are not used as same-game inputs and do not establish causation.

## Book recommender

The content-based book recommender uses up to ten favourite books and compares:

- normalised themes and detailed Open Library subjects;
- metadata-derived writing-style proxies;
- author;
- broad length band;
- publication era and language; and
- bounded reader-interest evidence, used as a quality prior rather than a substitute for similarity.

It excludes selected books, limits repeated authors and returns one main list plus up to three theme lists. Each recommendation explains why it matched.

Recommendations stay in the favourites' language. Missing language data defaults to English, and English edition titles are used where available.

Open Library does not provide prose-level style data or user-level ratings. Style is therefore an estimate based on metadata.

On Cloudflare, the original Python recommendation model runs in the browser via Pyodide. Search uses the [Open Library Search API](https://openlibrary.org/dev/docs/api/search) directly, with bounded results, timeouts, caching and request spacing. A local catalogue is used if Open Library is unavailable. The Flask client retains server-side requests and retries for local use.

## Data

The AFL model uses derived match, team and player data from [Wheelo Ratings](https://www.wheeloratings.com/) and fixtures/results from the [Squiggle API](https://api.squiggle.com.au/). AFL ingestion runs locally or in GitHub Actions, using cached, low-volume requests.

Before treating the scheduled Wheelo ingestion as a long-term public production feed, obtain written confirmation that this automated derived use is acceptable. AFL Tables and the fitzRoy/TORP datasets are documented fallback and validation sources.

## Local use

From `app/`, create a virtual environment, install `requirements-dev.txt`, then run:

```bash
python scripts/train_model.py
pytest -q
gunicorn --bind 127.0.0.1:8000 --workers 1 --threads 4 app:app
```

Training runs locally and does not require Azure ML or paid compute. Source snapshots are cached under `app/data/raw/` and are intentionally excluded from Git. The trained model, evaluation report, and next-round prediction snapshot under `app/artifacts/` are deployed with the app.

Optional environment settings can be placed in `app/.env`:

```dotenv
AFL_DATABASE_ENABLED=false
AFL_DATABASE_READ_ENABLED=false
AFL_HOLDOUT_SEASON=2022
AFL_START_SEASON=2012
AFL_CURRENT_SEASON=2026
SQUIGGLE_CONTACT=your-contact-address
OPEN_LIBRARY_CONTACT=monitored-contact@example.com
```

The website and local development use versioned prediction files. No Azure credentials or SQL database are required.

## Hosting and updates

The live website is [sam-speed-models.pages.dev](https://sam-speed-models.pages.dev). See [CLOUDFLARE.md](CLOUDFLARE.md) for deployment, free-plan limits and the Azure retirement record.

The former Azure Terraform configuration is archived as `legacy/azure/main.tf.disabled` so it cannot accidentally provision paid resources from the repository root. SQL helper scripts remain for historical reference only. Private database and infrastructure backups are excluded from Git.

`.github/workflows/refresh-predictions.yml` trains and validates in GitHub Actions every Tuesday, then commits the model artifacts to `main`. Cloudflare Pages builds from `main`. No Azure refresh token or database is used. `AFL_CURRENT_SEASON` remains explicit (2026); update it when the next season feed is available.

Local Flask endpoints (see [Cloudflare route compatibility](CLOUDFLARE.md#route-compatibility) for the public static deployment):

- `/` — model chooser
- `/afl` — AFL prediction website
- `/books` — interactive book recommender
- `/api/books/search?q=...` — bounded favourite-book search
- `/api/books/recommend` — explainable themed recommendations
- `/api/books/model` — book model card and limitations
- `/api/predictions` — current prediction snapshot
- `/api/model` — model card and evaluation
- `/health` — application health
- `/ready` — SQL readiness without exposing connection details

Predictions are probabilistic and intended for analysis and entertainment, not betting advice.
