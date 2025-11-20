
# # main.py

# import uuid
# import inspect
# import os
# import shutil
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from templates import TEMPLATES

# app = FastAPI()

# # Allow all origins for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Create resume-pdfs folder automatically
# PDF_FOLDER = "resume-pdfs"
# os.makedirs(PDF_FOLDER, exist_ok=True)

# # Serve PDF files
# app.mount("/files", StaticFiles(directory=PDF_FOLDER), name="files")

# # Track current template index
# current_template_index = 0


# @app.post("/resume")
# async def unified_resume(data: dict):
#     global current_template_index

#     # Stop after 7 templates
#     if current_template_index >= len(TEMPLATES):
#         return {"message": "All templates finished", "last_template": True}

#     selected_template = TEMPLATES[current_template_index]
#     template_number = current_template_index + 1
#     current_template_index += 1

#     try:
#         # Run async or sync template
#         if inspect.iscoroutinefunction(selected_template):
#             pdf_path = await selected_template(data)
#         else:
#             pdf_path = selected_template(data)

#         # pdf_path is a string path returned by template
#         source_file_path = pdf_path

#         # Unique output file name
#         unique = uuid.uuid4().hex[:4].upper()
#         final_pdf_name = f"template_{template_number}_{unique}.pdf"
#         final_pdf_path = os.path.join(PDF_FOLDER, final_pdf_name)

#         # Copy PDF into resume-pdfs folder
#         shutil.copy(source_file_path, final_pdf_path)

#         # Return JSON response
#         return {
#             "status": "success",
#             "message": f"Resume template {template_number} created successfully!",
#             "download_link": f"http://127.0.0.1:8000/files/{final_pdf_name}"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# this is the main.py file with automatic delete pdf without calling api 



import inspect
import os
import shutil
import time
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from templates import TEMPLATES


PDF_FOLDER = "resume-pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)



#  UNIQUE FILE NAME GENERATOR

def get_unique_filename(base_name, folder):
    name, ext = os.path.splitext(base_name)
    counter = 1
    final_name = base_name

    while os.path.exists(os.path.join(folder, final_name)):
        final_name = f"{name}({counter}){ext}"
        counter += 1

    return final_name



#  CLEANUP OLD FILES (older than X hours)

def cleanup_old_pdfs(folder, max_age_hours):
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    for file in os.listdir(folder):
        fpath = os.path.join(folder, file)
        if os.path.isfile(fpath):
            age = now - os.path.getmtime(fpath)
            if age > max_age_seconds:
                try:
                    os.remove(fpath)
                except:
                    pass



#  BACKGROUND TASK (Deletes files every 60 seconds)

async def auto_cleanup_task():
    while True:
        cleanup_old_pdfs(PDF_FOLDER, max_age_hours=24)  # 2 min- (2/60)
        await asyncio.sleep(60)   # run every minute



#  FASTAPI APP WITH LIFESPAN STARTUP TASK

async def lifespan(app: FastAPI):
    asyncio.create_task(auto_cleanup_task())  # start background cleaner
    yield


app = FastAPI(lifespan=lifespan)

# Allow all origins for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/files", StaticFiles(directory=PDF_FOLDER), name="files")


current_template_index = 0



#  RESUME ENDPOINT

@app.post("/resume")
async def unified_resume(data: dict):
    global current_template_index

    if current_template_index >= len(TEMPLATES):
        return {"message": "All templates finished", "last_template": True}

    selected_template = TEMPLATES[current_template_index]
    template_number = current_template_index + 1
    current_template_index += 1

    try:
        pdf_path = selected_template(data)

        base_pdf_name = f"template_{template_number}.pdf"
        final_pdf_name = get_unique_filename(base_pdf_name, PDF_FOLDER)
        final_pdf_path = os.path.join(PDF_FOLDER, final_pdf_name)

        shutil.copy(pdf_path, final_pdf_path)

        return {
            "status": "success",
            "message": f"Resume template {template_number} created successfully!",
            "download_link": f"http://127.0.0.1:8000/files/{final_pdf_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
