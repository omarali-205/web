# backend/app.py
import os, json, uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import SessionLocal, init_db, Section, Resource
from models import ResourceIn, ResourceOut
from ai import fetch_transcript_for_youtube, analyze_resource_text, generate_learning_path, get_embedding

init_db()
app = FastAPI(title="LearnSync AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # للتطوير محليًا. عدل هذا عند النشر.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
def db_session():
    return SessionLocal()

# Endpoint لإضافة مورد (يجري تحليله فورًا)
@app.post("/add_resource", response_model=ResourceOut)
def add_resource(r: ResourceIn):
    db = db_session()
    try:
        # find or create section
        sec = db.query(Section).filter(Section.name == r.section_name).first()
        if not sec:
            sec = Section(id=str(uuid.uuid4()), name=r.section_name)
            db.add(sec); db.commit(); db.refresh(sec)

        # get metadata
        title = None
        thumbnail = None
        description = ""
        # crude extraction for YouTube
        if "youtube" in r.url or "youtu.be" in r.url:
            # title guess from URL as fallback
            from ai import extract_youtube_id
            title = r.url
            # fetch transcript
            transcript = fetch_transcript_for_youtube(r.url)
            description = transcript
            # thumbnail
            vid = extract_youtube_id(r.url)
            if vid:
                thumbnail = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        else:
            transcript = ""

        # analyze text
        analysis = analyze_resource_text(title or r.url, description, transcript, sec.name)
        emb = analysis['embedding']
        similarity = analysis['similarity']
        suitable = analysis['suitable']
        level = r.level or analysis['level']

        # save resource
        res = Resource(
            id=str(uuid.uuid4()),
            section_id=sec.id,
            url=r.url,
            title=title or r.url,
            description=description,
            thumbnail=thumbnail,
            level=level,
            similarity=similarity,
            suitable=suitable,
            embedding=json.dumps(emb)
        )
        db.add(res); db.commit(); db.refresh(res)

        return {
            "id": res.id,
            "url": res.url,
            "title": res.title,
            "description": res.description,
            "thumbnail": res.thumbnail,
            "level": res.level,
            "similarity": res.similarity,
            "suitable": res.suitable
        }
    finally:
        db.close()

# Endpoint لإرجاع الموارد مرتبة لكل Section
@app.get("/sections/{section_name}/path")
def get_section_path(section_name: str):
    db = db_session()
    try:
        sec = db.query(Section).filter(Section.name == section_name).first()
        if not sec:
            raise HTTPException(status_code=404, detail="Section not found")
        resources = []
        for r in sec.resources:
            emb = json.loads(r.embedding) if r.embedding else None
            resources.append({
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "thumbnail": r.thumbnail,
                "level": r.level,
                "similarity": r.similarity or 0,
                "embedding": emb
            })
        # generate path
        ordered = generate_learning_path(resources)
        return ordered
    finally:
        db.close()

# simple endpoint to list sections
@app.get("/sections")
def list_sections():
    db = db_session()
    try:
        secs = db.query(Section).all()
        return [{"id": s.id, "name": s.name, "count": len(s.resources)} for s in secs]
    finally:
        db.close()
