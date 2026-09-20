# AegisScan Local Security Demonstration Environment

This fixture is intentionally insecure and binds only to `127.0.0.1:8010`. It is for authorized local demonstrations only. It contains no real credentials, external calls, persistence, or destructive actions.

Start it with:

```powershell
python demo/security-lab/server.py
```

Open `http://127.0.0.1:8010` and configure AegisScan against that URL. The server exposes intentionally incomplete headers, weak cookie attributes, permissive CORS, a harmless debug configuration endpoint, and a small source pattern for local scanner testing.
