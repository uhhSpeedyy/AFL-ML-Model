# Retired Azure infrastructure

These files are historical reference only. The `.disabled` extension prevents Terraform from loading them. The live site uses Cloudflare Pages and GitHub Actions; do not rename or apply this configuration unless you intentionally want to create paid Azure resources again. Database helper scripts under `app/sql` and `app/scripts` are also retained only for reference.

Private state, variable files and the SQL data backup are kept outside version control in the ignored `private-backups/azure-retirement/` folder on the migration computer.
