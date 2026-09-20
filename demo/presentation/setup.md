# Demo Setup

1. Install backend packages with `pip install -r backend/requirements.txt`.
2. Install frontend packages with `cd frontend; npm install`.
3. Run `start_demo.bat` from the repository root.
4. Run `powershell -ExecutionPolicy Bypass -File demo/demo_check.ps1`.
5. Open `http://127.0.0.1:5173`.
6. Register the lab target at `http://127.0.0.1:8010` with local authorization.
7. Enable custom checks. Enable external scanners only when `demo_check.ps1` reports them installed.
8. Reset with `powershell -ExecutionPolicy Bypass -File demo/reset_demo.ps1`.
