# Contributing

Thank you for your interest in contributing to this project! Please take a moment to read through the minimum requirements below before opening a pull request.

## Development workflow

1. Install PHP 8.2 or newer with the extensions required by the application (`intl`, `gd`, `mysqli`, and `zip`).
2. Install Composer dependencies:
   ```bash
   composer install
   ```
3. Run the quality gates before pushing:
   ```bash
   composer lint
   composer stan
   composer test
   ```
4. Use `composer fmt` to automatically fix coding style issues when necessary. All commands have ANSI output enabled in CI,
   so feel free to add `--ansi` locally for the same experience.
5. Tag releases when you need a production Docker image — the CI workflow automatically builds and publishes to GHCR on tags.

## Pull requests

* Keep changes focused and include context in the pull request description.
* Ensure GitHub Actions checks are green. The CI pipeline runs composer validation, installs dependencies with cache reuse, executes linting, static analysis, unit tests, and on tags builds & publishes the production Docker image to GHCR.
* Add or update tests when you change application behaviour.

We appreciate your help in keeping the project healthy and maintainable!
