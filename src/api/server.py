from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uvicorn
from ..orchestrator.run_hybrid import HybridOrchestrator

app = FastAPI(title='Heilbronn Hybrid Traffic API')

DATA_DIR = Path('data')
OUTPUT_DIR = Path('output')
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

orchestrator = HybridOrchestrator(DATA_DIR, OUTPUT_DIR)

@app.post('/upload/osm')
async def upload_osm(file: UploadFile = File(...)):
    dest = DATA_DIR / 'heilbronn.osm'
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {'status': 'ok', 'path': str(dest)}

@app.post('/upload/gtfs')
async def upload_gtfs(file: UploadFile = File(...)):
    dest = DATA_DIR / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {'status': 'ok', 'path': str(dest)}

@app.post('/run')
async def run_pipeline(background_tasks: BackgroundTasks):
    background_tasks.add_task(orchestrator.run_full_pipeline)
    return {'status': 'started'}

@app.get('/results')
def get_results():
    res_file = OUTPUT_DIR / 'final_results.json'
    if not res_file.exists():
        return JSONResponse({'status': 'not ready'}, status_code=202)
    import json
    return json.loads(res_file.read_text())

if __name__ == '__main__':
    uvicorn.run('api.server:app', host='0.0.0.0', port=8000, reload=True)
