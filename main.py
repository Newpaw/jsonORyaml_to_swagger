import os
import sqlite3
import json
import re
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.background import BackgroundTask
from typing import Dict
import yaml
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("OPENAPI_DB_PATH", "openapi_specs.db")

app = FastAPI()

ROOT_PAGE_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Upload OpenAPI Spec</title>
    <style>
      body {{ font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; padding: 0; }}
      .container {{ max-width: 500px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 32px; }}
      h1 {{ font-size: 1.6em; margin-bottom: 0.5em; }}
      form {{ display: flex; flex-direction: column; gap: 1em; }}
      label {{ font-weight: bold; }}
      input[type="text"], input[type="file"] {{ padding: 0.5em; border: 1px solid #ccc; border-radius: 4px; }}
      button {{ background: #007bff; color: #fff; border: none; padding: 0.7em 1.2em; border-radius: 4px; font-size: 1em; cursor: pointer; }}
      button:hover {{ background: #0056b3; }}
      .message {{ margin-top: 1em; padding: 1em; border-radius: 4px; }}
      .error {{ background: #ffe5e5; color: #b30000; border: 1px solid #ffb3b3; }}
      .success {{ background: #e6ffe6; color: #006600; border: 1px solid #99ff99; }}
      .urls {{ margin-top: 1em; }}
      .urls a {{ display: block; color: #007bff; text-decoration: none; margin-bottom: 0.3em; }}
      .urls a:hover {{ text-decoration: underline; }}
      .instructions {{ background: #f1f1f1; padding: 1em; border-radius: 4px; margin-bottom: 1em; }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Upload OpenAPI Specification</h1>
      <div class="instructions">
        <ul>
          <li>Select a valid OpenAPI JSON or YAML file from your computer.</li>
          <li>Enter a unique <b>spec ID</b> (letters, numbers, underscores).</li>
          <li>After upload, you will get links to the Swagger UI and raw JSON for your spec.</li>
        </ul>
      </div>
      {message_block}
      <form method="post" enctype="multipart/form-data">
        <label for="spec_id">Spec ID:</label>
        <input type="text" id="spec_id" name="spec_id" required pattern="^[A-Za-z0-9_\\-]+$" maxlength="50" />

        <label for="file">OpenAPI JSON or YAML file:</label>
        <input type="file" id="file" name="file" accept=".json,.yaml,.yml,application/json,application/x-yaml,text/yaml" required />

        <button type="submit">Upload</button>
      </form>
      {urls_block}
    </div>
  </body>
</html>
"""

SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
      *, *:before, *:after { box-sizing: inherit; }
      body { margin:0; background: #fafafa; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function() {
        const ui = SwaggerUIBundle({
          url: window.location.pathname.replace('/docs/', '/openapi/'),
          dom_id: '#swagger-ui',
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
          ],
          layout: "BaseLayout",
          deepLinking: true
        });
        window.ui = ui;
      };
    </script>
  </body>
</html>
"""

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS openapi_specs (
            spec_id TEXT PRIMARY KEY,
            spec_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def get_spec(spec_id: str):
    with get_db() as conn:
        cur = conn.execute("SELECT spec_json FROM openapi_specs WHERE spec_id = ?", (spec_id,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

def upsert_spec(spec_id: str, spec: dict):
    now = datetime.utcnow().isoformat()
    spec_json = json.dumps(spec)
    with get_db() as conn:
        try:
            conn.execute("""
                INSERT INTO openapi_specs (spec_id, spec_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(spec_id) DO UPDATE SET
                    spec_json=excluded.spec_json,
                    updated_at=excluded.updated_at
            """, (spec_id, spec_json, now, now))
            conn.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

def is_valid_openapi(spec: dict):
    return isinstance(spec, dict) and "openapi" in spec and "info" in spec

def render_root_page(message: str = "", success: bool = False, urls: list = None):
    message_block = ""
    if message:
        css_class = "success" if success else "error"
        message_block = f'<div class="message {css_class}">{message}</div>'
    urls_block = ""
    if urls:
        urls_block = '<div class="urls"><b>Access your documentation:</b>' + "".join(
            f'<a href="{url}" target="_blank">{url}</a>' for url in urls
        ) + "</div>"
    return ROOT_PAGE_HTML.format(message_block=message_block, urls_block=urls_block)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def root_page():
    return HTMLResponse(render_root_page())

@app.post("/", response_class=HTMLResponse)
async def upload_form(
    spec_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Validate spec_id
    if not re.match(r"^[A-Za-z0-9_\-]+$", spec_id):
        return HTMLResponse(render_root_page("Invalid spec ID. Use only letters, numbers, underscores, or hyphens.", False), status_code=400)
    # Validate file extension
    filename = file.filename.lower()
    if not (filename.endswith(".json") or filename.endswith(".yaml") or filename.endswith(".yml")):
        return HTMLResponse(render_root_page("File must be a .json, .yaml, or .yml file.", False), status_code=400)
    # Read and parse file
    try:
        contents = await file.read()
        if filename.endswith(".json"):
            spec = json.loads(contents)
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            spec = yaml.safe_load(contents)
        else:
            return HTMLResponse(render_root_page("Unsupported file type.", False), status_code=400)
    except Exception:
        return HTMLResponse(render_root_page("Uploaded file is not valid JSON or YAML.", False), status_code=400)
    if not is_valid_openapi(spec):
        return HTMLResponse(render_root_page("File is not a valid OpenAPI spec (missing 'openapi' or 'info').", False), status_code=400)
    # Store the spec in DB
    try:
        upsert_spec(spec_id, spec)
    except HTTPException as e:
        return HTMLResponse(render_root_page(str(e.detail), False), status_code=500)
    urls = [
        f"/docs/{spec_id}",
        f"/openapi/{spec_id}"
    ]
    msg = f"Spec '<b>{spec_id}</b>' uploaded successfully."
    return HTMLResponse(render_root_page(msg, True, urls))

@app.post("/upload/{spec_id}")
async def upload_openapi_spec(spec_id: str, request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "yaml" in content_type:
            body = await request.body()
            spec = yaml.safe_load(body)
        else:
            spec = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON or YAML")
    if not is_valid_openapi(spec):
        raise HTTPException(status_code=400, detail="File is not a valid OpenAPI spec (missing 'openapi' or 'info').")
    upsert_spec(spec_id, spec)
    return {"message": f"Spec '{spec_id}' uploaded successfully."}

@app.get("/docs/{spec_id}", response_class=HTMLResponse)
async def serve_swagger_ui(spec_id: str):
    spec = get_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    return HTMLResponse(content=SWAGGER_UI_HTML)

@app.get("/openapi/{spec_id}", response_class=JSONResponse)
async def serve_openapi_json(spec_id: str):
    spec = get_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    return JSONResponse(content=spec)
