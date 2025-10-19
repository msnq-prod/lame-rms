# Contributing

Thank you for helping improve AdamRMS! This document outlines the expected branch
workflow, commit style, and verification steps so that changes stay predictable and
maintainable.

## Branch workflow

- Work happens in short-lived branches cut from `main`.
- Use descriptive prefixes such as `feature/`, `bugfix/`, or `chore/` followed by a
  succinct summary (`feature/resource-filters`).
- Keep commits focused; open a draft pull request early if you need feedback.
- Rebase your branch on top of the latest `main` before requesting review to keep the
  history linear.

## Commit style

We follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(optional scope): <imperative summary>
```

Common types include `feat`, `fix`, `docs`, `refactor`, and `chore`. Scopes should be
short identifiers that clarify the area touched. Example:

```
feat(auth): allow SSO login via Azure AD
```

## Quality checks

Run the automated checks locally before pushing:

```bash
composer lint   # coding standards (PHP_CodeSniffer)
composer stan   # static analysis (PHPStan)
composer test   # unit tests (PHPUnit)
```

Format PHP files when needed with `composer fmt`.

## Database migrations

Schema changes are managed through [Phinx](https://book.cakephp.org/phinx/latest/).
After creating or editing migrations inside `db/migrations`, run them against the dev
stack:

```bash
make migrate
```

Seed data lives in `db/seeds` and can be reapplied with:

```bash
make seed
```

Ensure migrations and seeds complete without errors before opening a pull request.

## Opening a pull request

1. Confirm the quality checks and migrations have run successfully.
2. Fill out the pull request template, summarising the change and test coverage.
3. Await review — reviewers may request adjustments or additional test coverage.
4. Once approved, a project maintainer will merge the branch into `main`.

Thanks again for contributing!
