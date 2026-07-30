# Validation and release

Read this reference when validating a completed change or when deploy, install, upgrade, promotion, or production configuration was requested. Route a broad pre-deploy or release-readiness assessment to `forge-app-review`; use this reference for validation during build work and explicitly authorized release actions.

Use the repository's relevant tests and checks, and build Custom UI resources when applicable. Follow the core manifest-validation invariant. Do not deploy merely to compensate for missing local validation.

Before a consequential Forge command, retrieve its current documentation and confirm the exact app, environment, site, product, authorization, and any material version, permission, installation, migration, compatibility, licensing, or data effect. Retrieve the exact version, bulk-upgrade, rollout, sharing, or Marketplace guidance when the requested action implicates it. Never infer a live target or choose among multiple targets on the user's behalf.

For an explicitly authorized development deployment or installation, the retained helper can install dependencies, run `forge lint`, deploy, and install:

```bash
python3 -m scripts.deploy_forge_app \
  --app-dir <app-directory> \
  --site <confirmed-site> \
  --product <confirmed-product> \
  --env <confirmed-environment>
```

Use `--deploy-only` when installation was not authorized. Do not use this helper for bulk upgrades, promotions, or production rollout decisions; retrieve and execute the exact current CLI workflow for those operations.

Report the target and result of release actions along with any remaining verification.

Official entries:

- CLI: <https://developer.atlassian.com/platform/forge/cli-reference/>
- Environments and versions: <https://developer.atlassian.com/platform/forge/environments-and-versions/>
- Deploy: <https://developer.atlassian.com/platform/forge/cli-reference/deploy/>
- Install: <https://developer.atlassian.com/platform/forge/cli-reference/install/>
- Version commands: <https://developer.atlassian.com/platform/forge/cli-reference/version/>
- Distribution: <https://developer.atlassian.com/platform/forge/distribute-your-apps/>
