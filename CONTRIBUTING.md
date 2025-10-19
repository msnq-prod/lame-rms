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
4. Use `composer fmt` to automatically fix coding style issues when necessary.

## Pull requests

* Keep changes focused and include context in the pull request description.
* Ensure GitHub Actions checks are green. The CI pipeline runs linting, static analysis, tests, and on tags will build & publish the production Docker image to GHCR.
* Add or update tests when you change application behaviour.

We appreciate your help in keeping the project healthy and maintainable!
