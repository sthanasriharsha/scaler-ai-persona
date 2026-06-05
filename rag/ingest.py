"""
RAG Ingest Script - Final Fixed Production Copy
Run once: python ingest.py
"""
import os
import re
import time
import requests
import tiktoken
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from google import genai
from dotenv import load_dotenv

# Absolute path resolution that forces Windows to find the exact file
ROOT_DIR = Path(__file__).resolve().parent.parent
backend_env_path = ROOT_DIR / "backend" / ".env"

if backend_env_path.exists():
    load_dotenv(dotenv_path=str(backend_env_path))
else:
    load_dotenv()

# Grab credentials from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "sriharsha-persona")
GITHUB_USERNAME = "sthanasriharsha"  # Your username is correctly added here
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Clear validation checks to prevent silent failures
if not PINECONE_API_KEY:
    print(f"❌ Error: PINECONE_API_KEY is blank or missing inside your .env file!")
    exit(1)

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY is blank or missing inside your .env file!")
    exit(1)

# Configure Gemini Client API
client = genai.Client(api_key=GEMINI_API_KEY)

# Use standard tokenizer approximation for text trunk splitting
enc = tiktoken.get_encoding("cl100k_base")

RESUME_TEXT = """
Name: Gundumalla Sthana Sriharsha
Email: sthanasriharsha@gmail.com | Phone: +91-8096414909
LinkedIn: ://linkedin.com | GitHub: ://github.com

PROFESSIONAL SUMMARY
AI & Data Science graduate with hands-on experience in Python, AI/ML, and backend systems.
AI/ML Intern at C-DAC working on real-world software and AI solutions.

WORK EXPERIENCE
AI/ML Intern — C-DAC, Thiruvananthapuram (Feb 2026 – Present)
- Computer Vision and NLP pipelines using TensorFlow & OpenCV
- Optimised ML inference pipelines for real-world deployment
- Data preprocessing, collaboration on research AI projects

AI/ML Intern — Google for Developers, AICTE (Remote, Oct–Dec 2024)

PROJECTS
Pose Normalisation (Python, DWPose, OpenCV, NumPy)
- Pipeline extracting & normalising human pose keypoints across video frames
- Scaling, translation, alignment ensuring pose invariance
- Standardising skeletal representations across heterogeneous datasets

Word Sense Disambiguation (NLP, WordNet, PyTorch)
- NLP system detecting ambiguous words and determining correct meaning from context
- Combined WSD with a word scoring mechanism

Low Light Image Enhancement (Python, OpenCV, NumPy, Flask)
- Adaptive filtering and histogram equalisation for low-light images
- Deployed as Flask REST API for real-time use

AI Doc Assistant (Streamlit, Google Gemini API, Python)
- Google Gemini API for document Q&A and automated summarisation

TECHNICAL SKILLS
Python, Java | LangChain, RAG, Prompt Engineering, Claude, OpenAI
TensorFlow, OpenCV, Scikit-learn, NumPy, Pandas, Flask, Whisper, Streamlit
HTML, CSS, JavaScript | SQL

EDUCATION
B.Tech CSE (AI & Data Science), GNIT Ibrahimpatnam — CGPA 7.38 (Dec 2021–Jun 2025)
Intermediate MPC, NRI Jr College Bachupally — 92.8%
SSC, TSMS Kulakacharla — CGPA 9.0

CERTIFICATIONS
- Programming Foundations with Python — Cisco Networking Academy
- Web Development — IBM Skills Build
- Introduction to Data Science — Cisco Networking Academy
- Machine Learning Professional Certification — Altair
"""

BIO_TEXT = """
Sriharsha is a hands-on AI engineer with real production experience from his C-DAC internship.
He built computer vision pipelines processing real video data for deployment.
He is comfortable with the full ML stack: data preprocessing, model training, API deployment.

Why Sriharsha fits Scaler AI Engineer Intern:
- Shipped real AI features in production at C-DAC (government R&D lab)
- Hands-on with LLMs, RAG, and agentic pipelines
- Strong Python fundamentals, quick learner, can own tasks end-to-end
- Available immediately, based in Thiruvananthapuram
- Clear communicator, works well in teams

For interview scheduling, availability can be checked at ://cal.com
"""

def chunk_text(text, source, max_tokens=300):
    sentences = re.split(r'(?<=[.!\n])\s+', text.strip())
    chunks, current, current_tokens = [], [], 0
    for sent in sentences:
        t = len(enc.encode(sent))
        if current_tokens + t > max_tokens and current:
            chunks.append({"text": " ".join(current), "source": source})
            current, current_tokens = [sent], t
        else:
            current.append(sent)
            current_tokens += t
    if current:
        chunks.append({"text": " ".join(current), "source": source})
    return chunks

def fetch_github_repos():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        # Fixed path concatenation here
        resp = requests.get(f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
                            headers=headers, timeout=10, params={"per_page": 30})
        if resp.status_code != 200:
            print(f"⚠️ GitHub API returned status code: {resp.status_code}")
            return []
        repos = resp.json()
        chunks = []
        for repo in repos:
            if isinstance(repo, dict) and not repo.get("fork"):
                name = repo.get("name", "")
                desc = repo.get("description", "") or ""
                readme_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{name}/main/README.md"
                try:
                    r = requests.get(readme_url, timeout=8)
                    text = f"Repo: {name}\nDescription: {desc}\n\n{r.text[:3000]}" if r.status_code == 200 else f"Repo: {name}\nDescription: {desc}"
                    chunks.extend(chunk_text(text, f"github/{name}"))
                    time.sleep(0.1)
                except Exception:
                    pass
        return chunks
    except Exception as e:
        print(f"GitHub fetch failed: {e}")
        return []

def embed_batch(texts):
    results = []
    for text in texts:
        try:
            r = client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=text,
            )
            results.append(r.embeddings[0].values)
            time.sleep(0.2)
        except Exception as e:
            print(f"Embedding failed for block: {e}")
            results.append(None)
    return results

def upsert_chunks(index, chunks):
    for i in range(0, len(chunks), 50):
        batch = chunks[i:i+50]
        vectors = embed_batch([c["text"] for c in batch])
        
        index_payload = []
        for j in range(len(batch)):
            if vectors[j] is None:
                print(f"Skipping chunk-{i+j} due to embedding failure")
                continue
            index_payload.append((
                f"chunk-{i+j}",
                vectors[j],
                {"text": batch[j]["text"], "source": batch[j]["source"]}
            ))
        
        if index_payload:
            index.upsert(vectors=index_payload)
        print(f"Upserted {i+len(batch)}/{len(chunks)}")
        time.sleep(0.5)

def main():
    print("Init Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check index and force name creation parameters
    active_indexes = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in active_indexes:
        print(f"Creating new serverless index '{INDEX_NAME}' with 3072 dimensions...")
        pc.create_index(
            name=INDEX_NAME, 
            dimension=3072, 
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print("Waiting for Pinecone to boot up the cloud server...")
        time.sleep(10)
        
    index = pc.Index(INDEX_NAME)
    all_chunks = []
    
    print("Chunking resume...")
    all_chunks.extend(chunk_text(RESUME_TEXT, "resume"))
    
    print("Chunking bio...")
    all_chunks.extend(chunk_text(BIO_TEXT, "bio"))
    
    print("Fetching GitHub repos...")
    gh = fetch_github_repos()
    all_chunks.extend(gh)
    print(f"Fetched {len(gh)} chunks from GitHub.")
    
    print(f"\nTotal: {len(all_chunks)} chunks. Upserting...")
    upsert_chunks(index, all_chunks)
    print("Done database seeding!", index.describe_index_stats())

if __name__ == "__main__":
    main()