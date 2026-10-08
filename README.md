# Todo API

## Run the stack

Copy `.env.example` to `.env`, then run:

```sh
docker compose up --build
```

The API is available at `http://localhost:8000`. Postgres data is stored in
the named `postgres_data` volume.

## Storage architecture

The service and HTTP routes keep the same repository-facing behavior. Storage
was switched by replacing the SQLite implementation with
`PostgresTaskRepository`; routes call repository methods rather than issuing
SQL themselves. The schema is created by `schema.sql` during application
startup.

## Persistence check

1. Start the stack with `docker compose up --build`.
2. Create a task:

   ```sh
   curl -X POST http://localhost:8000/tasks ^
     -H "Content-Type: application/json" ^
     -d "{\"title\":\"survives restart\"}"
   ```

3. Stop and remove the containers, but keep the volume:

   ```sh
   docker compose down
   docker compose up
   ```

4. `GET http://localhost:8000/tasks` still returns the created task. The
   `postgres_data` volume preserves it across app and container restarts.
