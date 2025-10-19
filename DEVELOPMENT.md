# Development Guide

This guide walks you through bringing the AdamRMS stack online locally and highlights
recurring commands and troubleshooting tips.

## Quick Start

1. **Install prerequisites and clone the repo.** Make sure Docker, Docker Compose, and GNU Make are
   available on your machine. Clone the repository and copy the default environment settings with:
   ```bash
   git clone https://github.com/adam-rms/adam-rms.git
   cd adam-rms
   cp .env.example .env
   ```
2. **Provision the stack.** From the project root run:
   ```bash
   make setup
   ```
   The command builds the containers, installs PHP dependencies via Composer, and
   applies database migrations and seeds.
3. **Open the services.** Once the containers report healthy status, visit the web
   UI at http://localhost:8080/. Supporting tools are available at:
   - Adminer: http://localhost:8081/
   - Mailhog: http://localhost:8025/
   - MinIO API: http://localhost:9000/ (console at http://localhost:9001/)

## Make commands

| Command | Description |
| --- | --- |
| `make setup` | Build containers, install Composer dependencies, run migrations and seeds. |
| `make up` | Start the Docker services defined in `docker-compose.dev.yml`. |
| `make down` | Stop and remove the services. |
| `make logs` | Tail the combined logs of all services. |
| `make sh` | Open an interactive shell inside the PHP-FPM container. |
| `make migrate` | Run database migrations for the configured environment. |
| `make seed` | Execute database seeders. |
| `make xdebug:on` / `make xdebug:off` | Toggle the Xdebug extension inside the PHP container. |

## Troubleshooting

- **Ports already in use.** Stop any local services bound to ports 8080, 8081, 8025,
  9000, or 9001, then re-run `make up`.
- **Database migrations fail.** Ensure the containers are running (`make up`) and
  remove the cached volumes if the schema is inconsistent:
  ```bash
  make down
  docker volume rm lame-rms_db_data lame-rms_minio_data
  make setup
  ```
- **Composer cannot reach the internet.** Retry once your connection is restored or
  configure a proxy via environment variables before running `make setup`.
- **Need a fresh start.** Stop the stack with `make down`, delete the `.env` file if
  you want to reconfigure credentials, then repeat the Quick Start steps.
