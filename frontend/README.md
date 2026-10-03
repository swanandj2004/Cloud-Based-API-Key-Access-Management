# KeyVault Frontend

React + Vite frontend for the Cloud-Based API Key Access Management FastAPI project.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

By default the frontend calls:

`http://127.0.0.1:8000`

To change it, set:

```env
VITE_API_BASE_URL=http://your-fastapi-host:8000
```

## Backend endpoints used

- POST `/user/login`
- GET `/get/all/roles`
- GET `/get/all/users`
- GET `/get/all/keys`
- GET `/get/user/keys/{id}`
- POST `/create/key`
- DELETE `/delete/key/{id}`

Admin UI is enabled when the JWT `role` claim equals `8`, matching the backend's current `required_role`.

## Important backend note

The current `/create/key` endpoint returns only:

```json
{"status":"success","message":"API Key created successfully"}
```

The Create Key dialog therefore cannot display the newly generated plaintext key unless the backend is changed to return it, for example:

```python
return {
    "status": "success",
    "message": "API Key created successfully",
    "api_key": api_key
}
```

Also, the backend currently decrypts and returns plaintext API keys from admin GET endpoints. Treat those responses as sensitive.
