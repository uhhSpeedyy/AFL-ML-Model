# Free hosting options

**Update:** Cloudflare migration implementation and setup instructions are now in [CLOUDFLARE.md](CLOUDFLARE.md). The comparison below records the earlier investigation.

Checked 7 September 2026. The current app is Python/Flask with saved AFL prediction artifacts and an interactive Open Library book recommender. Terraform configures Azure B1 hosting, SQL connectivity, a private endpoint and private DNS. Moving traffic does not remove those resources or their costs.

## Recommended: Render Free for the full application

Render supports Python web services and Git-based updates. Its free service sleeps after 15 idle minutes and takes about a minute to wake. The workspace receives 750 free instance hours per month. Files changed at runtime disappear on sleep/restart, so keep trained models and prediction snapshots in Git and redeploy when they change. Do not use its free Postgres for permanent storage: it expires after 30 days.

Use one free web service with these settings:

- Repository: `uhhSpeedyy/AFL-ML-Model`
- Root directory: `app`
- Build: `pip install -r requirements.txt`
- Start: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app`
- Environment: `PYTHON_VERSION=3.11.11`, `AFL_DATABASE_ENABLED=false`, `AFL_DATABASE_READ_ENABLED=false`
- Health check: `/health`
- Leave `AFL_REFRESH_TOKEN` unset; train and refresh locally instead of loading the training stack into the small free server.

These settings are a migration proposal, not a verified Render deployment. Verify dependency installation and memory usage with both `/afl` and `/books` before switching. No database is needed for normal snapshot-based serving. Keep payment details unset to have services/builds stop at relevant usage limits instead of buying additional usage. Free-tier limits and policies can change.

Updates: run `python scripts/train_model.py` from `app` in the prepared local environment, run tests, commit the three `app/artifacts/` outputs, and push. Render can redeploy from the repository. Website code changes use the same Git workflow. Disable the existing Azure deployment and Azure refresh workflows when the migration is complete, or they will continue targeting Azure. A future GitHub Actions training workflow is possible; public repositories have free standard hosted runners, subject to GitHub's limits and policies.

## Other options

- **Cloudflare Pages:** static asset requests are free and unlimited, with 500 builds/month on Free. Good for exporting the AFL page and prediction JSON after local training. The existing Flask application and book recommendation endpoints require conversion or a separate backend; Pages is not a direct replacement for this app.
- **PythonAnywhere Free:** supports one Python web app, but restricted outbound internet access must be checked against Open Library, Squiggle and Wheelo. New free accounts have a one-month web-app expiry/renewal cycle. Less convenient for this particular API-backed site.
- **Azure F1:** investigate availability for this Linux app/region if retaining the Azure hostname is essential. Free shared compute has CPU quotas, and the existing VNet integration and SQL/private-network resources need separate changes. Changing B1 to F1 alone is not a complete zero-cost migration.

## Address and Azure shutdown

The `sam-speed.azurewebsites.net` address belongs to Azure and cannot be pointed to Render using DNS you control. Use the new provider's free subdomain, or move a custom domain you own (domain registration/renewal is a separate cost). A redirect served by Azure still requires that Azure app to remain available.

After a replacement is verified, back up any SQL history you want to retain and review/remove the unused billable Azure resources. Stopping the app or redirecting visitors does not delete its paid service plan. Do not run a blanket Terraform destroy without reviewing its resource list. No hosting resources or billing settings were changed during this investigation.

## Sources

- https://render.com/docs/free
- https://render.com/docs/deploy-flask
- https://developers.cloudflare.com/pages/functions/pricing/
- https://developers.cloudflare.com/pages/platform/limits/
- https://help.pythonanywhere.com/pages/FreeAccountsFeatures/
- https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans
- https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/avoid-charges-free-account
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
