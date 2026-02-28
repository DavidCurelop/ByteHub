# Contributing Guidelines

## Commit Message Convention

The recommended pattern follows the Conventional Commits specification.

### Format

```
<type>(<scope>): <short description>

<blank line>

<body>

<blank line>

<footer>
```

### Examples

```
feat(auth): add JWT authentication support

fix(api): fix email validation on /users/register

refactor(core): simplify repository interface
```

### Common Types

| Type | Meaning |
|------|---------|
| `feat` | new feature |
| `fix` | bug fix |
| `docs` | documentation only |
| `style` | formatting or lint changes |
| `refactor` | code change without feature or fix |
| `test` | adding or updating tests |
| `chore` | maintenance, dependencies, config changes |

### Example with body and footer

```
feat(users): implement password recovery

Added POST /users/recover-password endpoint with email token support.

BREAKING CHANGE: /users/reset-password now requires a recovery token.
Closes #142
```

## Branch Naming Convention

Branches should use a clear, consistent, and lowercase naming pattern.

### Format

```
<type>/<short-description>
```

Optionally include a ticket or issue number:

```
<type>/<ticket-id>-<short-description>
```

### Examples

```
feat/login-endpoint
fix/bug-142-invalid-email
docs/update-readme
refactor/user-service
```

### Recommended Types

- `feat-` – new features
- `fix-` – bug fixes
- `chore-` – maintenance or CI/CD changes
- `refactor-` – internal code restructuring
- `docs-` – documentation updates
- `test-` – testing-related branches

