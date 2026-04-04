"""Entry point for `python -m lms_backend.run` — stub."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("lms_backend.main:app", host="0.0.0.0", port=8000, reload=True)
