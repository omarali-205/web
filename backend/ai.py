# backend/ai.py
import os, json, math, tempfile
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import openai
import numpy as np

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise Exception("ضع OPENAI_API_KEY في المتغيرات البيئية")
openai.api_key = OPENAI_KEY

# ---------- Utilities ----------
def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a); b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    # استدعاء OpenAI Embeddings
    resp = openai.Embeddings.create(input=text, model=model)
    return resp['data'][0]['embedding']

# ---------- Transcript extraction ----------
def extract_youtube_id(url: str) -> Optional[str]:
    try:
        # يدعم youtube.com/watch?v=ID و youtu.be/ID
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "youtube.com" in url:
            # بحث عن v=
            import re
            m = re.search(r"v=([^&]+)", url)
            if m: return m.group(1)
    except Exception:
        return None
    return None

def fetch_transcript_for_youtube(url: str) -> str:
    vid = extract_youtube_id(url)
    if not vid:
        return ""
    try:
        t = YouTubeTranscriptApi.get_transcript(vid, languages=['ar','en'])
        # concat text
        full = " ".join([seg['text'] for seg in t])
        return full
    except (TranscriptsDisabled, NoTranscriptFound):
        # حاول استخدام auto-generated captions أو فارغ
        return ""
    except Exception:
        return ""

# ---------- Higher level functions ----------
def analyze_resource_text(title: str, description: str, text: str, section_name: str):
    """
    Returns: dict with embedding, similarity, suitability(boolean), inferred_level
    """
    # Build a single textual representation
    combined = "Title: " + title + "\nDescription: " + (description or "") + "\nContent: " + (text or "")
    # get embedding
    emb = get_embedding(combined)
    # get section embedding
    s_emb = get_embedding(section_name)
    sim = cosine_similarity(emb, s_emb)
    # infer level (very simple heuristic using keywords)
    lvl = infer_level_from_text(combined)
    suitable = sim >= 0.45  # threshold قابل للتعديل بعد التجربة
    return {
        "embedding": emb,
        "similarity": sim,
        "suitable": suitable,
        "level": lvl
    }

def infer_level_from_text(text: str) -> str:
    t = text.lower()
    # كلمات مفتاحية بسيطة
    if any(k in t for k in ["beginner","intro","مقدمة","أساس","basic","مبتدئ"]):
        return "مبتدئ"
    if any(k in t for k in ["intermediate","متوسط","متقدم","advanced","project","practical","مشروع"]):
        return "متوسط"
    # default
    return "متوسط"

def generate_learning_path(resources: List[Dict]) -> List[Dict]:
    """
    resources: list of dicts that contain 'id', 'title', 'embedding', 'level', 'similarity'
    Strategy:
      - cluster by similarity (simple agglomerative via cosine distance using sklearn or by k-means on embeddings)
      - within cluster, sort by level (مبتدئ->متوسط->متقدم) and by similarity descending.
    """
    from sklearn.cluster import AgglomerativeClustering
    import numpy as np

    if not resources:
        return resources

    X = np.array([r['embedding'] for r in resources])
    n_clusters = min(3, max(1, len(resources)//3))  # heuristic
    # if only 1 resource, return as is
    if len(resources) == 1:
        return resources

    # Agglomerative clustering on embeddings with cosine affinity
    try:
        clustering = AgglomerativeClustering(n_clusters=n_clusters, affinity='cosine', linkage='average')
        labels = clustering.fit_predict(X)
    except Exception:
        # fallback: single cluster
        labels = [0]*len(resources)

    # group by label
    grouped = {}
    for idx, lbl in enumerate(labels):
        grouped.setdefault(lbl, []).append(resources[idx])

    # order clusters by average similarity descending
    cluster_order = sorted(grouped.items(), key=lambda kv: -np.mean([r.get('similarity',0) for r in kv[1]]))
    ordered = []
    level_rank = {'مبتدئ': 1, 'متوسط': 2, 'متقدم': 3}
    for lbl, group in cluster_order:
        # sort within group
        group_sorted = sorted(group, key=lambda r: ((level_rank.get(r.get('level'),'2') if r.get('level') else 2), -r.get('similarity',0)))
        ordered.extend(group_sorted)
    return ordered
