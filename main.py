
# main.py

import uuid
import inspect
import os
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from templates import TEMPLATES

app = FastAPI()

# Allow all origins for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create resume-pdfs folder automatically
PDF_FOLDER = "resume-pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)

# Serve PDF files
app.mount("/files", StaticFiles(directory=PDF_FOLDER), name="files")

# Track current template index
current_template_index = 0


@app.post("/resume")
async def unified_resume(data: dict):
    global current_template_index

    # Stop after 7 templates
    if current_template_index >= len(TEMPLATES):
        return {"message": "All templates finished", "last_template": True}

    selected_template = TEMPLATES[current_template_index]
    template_number = current_template_index + 1
    current_template_index += 1

    try:
        # Run async or sync template
        if inspect.iscoroutinefunction(selected_template):
            pdf_path = await selected_template(data)
        else:
            pdf_path = selected_template(data)

        # pdf_path is a string path returned by template
        source_file_path = pdf_path

        # Unique output file name
        unique = uuid.uuid4().hex[:4].upper()
        final_pdf_name = f"template_{template_number}_{unique}.pdf"
        final_pdf_path = os.path.join(PDF_FOLDER, final_pdf_name)

        # Copy PDF into resume-pdfs folder
        shutil.copy(source_file_path, final_pdf_path)

        # Return JSON response
        return {
            "status": "success",
            "message": f"Resume template {template_number} created successfully!",
            "download_link": f"http://127.0.0.1:8000/files/{final_pdf_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
