from fastapi import FastAPI, BackgroundTasks
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os

from client_app.core import ShareNotesClient
from client_app import downloader, config