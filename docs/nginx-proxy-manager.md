# Nginx Proxy Manager setup

Use the host-based Nginx Proxy Manager to publish only the frontend.

1. Create a new proxy host.
2. Set the **Domain Names** field to the VPS IP, or leave it blank if your NPM setup requires a default host.
3. Forward hostname: `127.0.0.1`
4. Forward port: `3000`
5. Enable Websockets Support.
6. Leave backend, Redis, and PostgreSQL unpublished; they stay internal to Docker.

## Backend access

If you want the FastAPI backend reachable from the host or a second proxy host:

1. Forward hostname: `127.0.0.1`
2. Forward port: `8000`
3. Use a separate proxy host like `api.your-ip-or-domain`

## Multiple projects

- Give each project its own folder.
- Set a different `FRONTEND_HOST_PORT` in that project's `.env`.
- Point each NPM proxy host at that project’s unique loopback port.

## Notes

- If you later add a domain, just change the proxy host target; the app container setup does not need to change.
- The backend remains reachable only from the Next.js container unless you explicitly expose it on localhost.
