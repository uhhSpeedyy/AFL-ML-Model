# Cloudflare migration

Project: `sam-speed-models`. Production URL: https://sam-speed-models.pages.dev. Initial deployment and public routes verified on 7 September 2026. The first GitHub refresh completed successfully and committed model artifacts to `main`.

## Architecture

The public website is a static Cloudflare Pages deployment with no paid Workers,
SQL database, Azure host, or server-side model process. The homepage and AFL page
are exported from the existing Flask templates. The AFL JSON endpoints are
exported with each deployment. The book page runs the **original Python ranking
model**, rather than a rewritten approximation, in a dedicated browser Web Worker
using Pyodide 314.0.6. Pyodide and the model code are served by Cloudflare too.

The initial public bundle is about 13 MiB; the Python runtime loads only on first
book search or recommendation. Browser caching reduces repeat downloads. Modern
browsers with JavaScript and WebAssembly are required. Open Library search and
cover requests remain external, as they were before. Google Fonts is unchanged.

Favourites stay in browser storage. Search text and derived theme queries go
directly to Open Library with no credentials. Requests are bounded, time out after
12 seconds, are spaced at least 1.1 seconds apart in each worker, and successful
results are cached for ten minutes (50 entries maximum). Upstream failures use the
existing curated fallback catalogue. There is no central user database.

## Build and deployment

Cloudflare Pages Git integration settings:

- Repository: `uhhSpeedyy/AFL-ML-Model`
- Production branch: `main`
- Framework preset: None
- Root directory: repository root
- Build command: `pip install -r cloudflare/requirements.txt && python cloudflare/build.py && python cloudflare/make_test_cases.py && node cloudflare/test_runtime.mjs`
- Build output directory: `cloudflare/dist`
- Python version: 3.11
- Plan: Free

No API keys, Azure credentials, database settings or paid services are required.
Each push to the production branch triggers a Cloudflare build. Preview branches
can be disabled if unnecessary. Only the allowlisted public output folder is
uploaded; `.env`, Terraform state, raw AFL data and the trained joblib binary are
excluded. The Pyodide download is pinned and SHA-512 verified.

Cloudflare's dashboard is the source of truth for the published URL and deployment
status. A migration is not complete until that URL, the AFL JSON snapshot and the
book recommendation flow have been checked after deployment.

## Updating the AFL model

`.github/workflows/refresh-predictions.yml` trains on a standard GitHub-hosted Linux
runner each Tuesday at 00:30 UTC, validates the model and browser runtime, and
commits the three model artifacts to `main`. Cloudflare's GitHub app then builds
the updated site. Use Actions → Refresh AFL predictions → Run workflow for an
extra update. Automatic schedules can be delayed and are disabled by GitHub on
inactive public repositories after 60 days; check the Actions page if updates stop.

The runner caches public historical inputs; all current-season rounds are
revalidated, including rounds previously downloaded before their last game ended.
Model selection still protects the 2022 holdout. `AFL_CURRENT_SEASON` defaults to
2026 and must be updated when the next season's source data is available. This is
intentional: do not advance the year automatically to a missing feed.

GitHub Actions standard runners are free for public repositories. Do not switch
this repository to private, use larger runners, raise paid storage limits, or add
paid Cloudflare products if zero hosting spend is the requirement. Cloudflare
Pages Free currently includes 500 builds per month and free static requests;
weekly updates fit comfortably within that allowance. Free plan policies can
change.

Local validation:

```sh
python -m pip install -r app/requirements-dev.txt
pytest -q app/tests
python cloudflare/build.py
python cloudflare/make_test_cases.py
node cloudflare/test_runtime.mjs
```

## Route compatibility

`/`, `/afl`, `/books`, `/api/predictions`, `/api/model`, `/api/books/model`, `/health`
and `/ready` remain available. Cloudflare serves the JSON aliases using `_redirects`.
Unknown routes return the custom 404 page rather than a successful homepage.

The interactive book UI uses browser operations instead of HTTP endpoints.
`/api/books/search`, `/api/books/recommend` and `/api/admin/refresh` are **not**
server APIs on the Cloudflare deployment; local Flask retains them for development.
The public site does not need these APIs. Any separate client using the old HTTP
endpoints would need adapting. Saved favourites on the Azure origin do not
automatically transfer to the new origin; reselect them on the new site.

## Azure retirement

On 7 September 2026, the full Azure inventory was reviewed and retirement was requested for the old website, B1 App Service plan, SQL server/database, private endpoint, virtual network, DNS zone, network security group, Log Analytics workspace and Network Watcher. These were the only resources in the subscription.

Before deletion, all four SQL user tables were exported to a private local backup and the saved JSON was read back to verify row counts: 2 model runs, 9 predictions, 2 prediction snapshots and 2 Users records. Database contents, infrastructure state and variable files are stored only in the ignored `private-backups/azure-retirement/` folder on the migration computer, with restricted file permissions. They are not published to GitHub or Cloudflare. Keep a private copy of that folder if moving computers.

The Azure deployment credentials and refresh token were removed from GitHub. The former Terraform files are archived under `legacy/azure/` with `.disabled` extensions. Local database access defaults to disabled. Historical SQL helper scripts remain available for reference; they are not part of the hosted site or update workflow.

The old `sam-speed.azurewebsites.net` address cannot be transferred to Cloudflare and is retired. Use https://sam-speed-models.pages.dev. Hosting and updates use the free services described above. Charges already accrued before cancellation can still appear on a final Azure bill.

## Sources

- [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Static hosting pricing](https://developers.cloudflare.com/pages/functions/pricing/)
- [GitHub integration](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Pyodide web workers](https://pyodide.org/en/stable/usage/webworker.html)
