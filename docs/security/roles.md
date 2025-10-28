# Role Matrix

| Slug | Name | Default | MFA Required | Permissions |
|---|---|---|---|---|
| auditor | Security Auditor | no | no | audit:events:read, auth:roles:read, auth:users:read |
| project_manager | Project Manager | yes | yes | assets:reserve, auth:users:read, crew:assign, projects:read, projects:write |
| system_admin | System Administrator | no | yes | audit:events:export, auth:mfa:reset, auth:roles:read, auth:roles:write, auth:users:read, auth:users:write |
| viewer | Operations Viewer | yes | no | assets:read, inventory:read, projects:read |
