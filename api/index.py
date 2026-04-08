"""
FastAPI entrypoint for Vercel deployment.
Vercel requires a proper WSGI/ASGI app — Streamlit can't run serverless.
This exposes the full command layer as a REST API.
Local dev: use `streamlit run app.py` instead.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from command_layer.decomposer import decompose
from command_layer.executor import execute_step
from command_layer.formatter import format_result

app = FastAPI(title="JeammyTool API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    command: str


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>JeammyTool</title>
      <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 60px auto; padding: 0 20px; }
        h1 { font-size: 2rem; }
        input { width: 100%; padding: 12px; font-size: 1rem; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        button { margin-top: 12px; padding: 12px 24px; background: #000; color: #fff; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
        button:hover { background: #333; }
        #result { margin-top: 32px; white-space: pre-wrap; background: #f5f5f5; padding: 20px; border-radius: 6px; display: none; }
        #steps { margin-top: 16px; font-size: 0.9rem; color: #555; }
        .step { padding: 4px 0; }
        .loading { color: #888; font-style: italic; }
      </style>
    </head>
    <body>
      <h1>AI Command Layer</h1>
      <p>Goal &rarr; Decompose &rarr; Execute &rarr; Result</p>
      <input id="cmd" type="text" placeholder="e.g. Analyze GitHub repo: anthropics/anthropic-sdk-python" />
      <br/>
      <button onclick="run()">Execute</button>
      <div id="steps"></div>
      <div id="result"></div>
      <script>
        async function run() {
          const cmd = document.getElementById('cmd').value.trim();
          if (!cmd) return;
          document.getElementById('steps').innerHTML = '<div class="loading">Decomposing...</div>';
          document.getElementById('result').style.display = 'none';
          const res = await fetch('/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
          });
          const data = await res.json();
          if (data.error) {
            document.getElementById('steps').innerHTML = '<b>Error:</b> ' + data.error;
            return;
          }
          document.getElementById('steps').innerHTML =
            data.steps.map(s => `<div class="step">✓ ${s.id}: ${s.description}</div>`).join('');
          document.getElementById('result').style.display = 'block';
          document.getElementById('result').textContent = data.result;
        }
        document.getElementById('cmd').addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
      </script>
    </body>
    </html>
    """


@app.post("/execute")
def execute_command(req: CommandRequest):
    try:
        steps = decompose(req.command)
        results = {}
        for step in steps:
            results[step["id"]] = execute_step(step, results)
        final = format_result(req.command, steps, results)
        return {"command": req.command, "steps": steps, "result": final}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
