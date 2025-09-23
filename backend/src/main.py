import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.ws import router as ws_router

origins = [
    'http://localhost',
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(ws_router)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True, host='localhost', port=8000)
