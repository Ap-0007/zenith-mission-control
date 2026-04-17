import os
import time
import psutil
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
import subprocess
import glob
import socket
import shutil

app = Flask(__name__)

# Constants
WORKSPACE_ROOT = "/Users/amogh/Downloads/anti/side_pro"

# --- RESILIENCE ROUTES ---
@app.route("/index.html")
@app.route("/static/index.html")
def redirect_to_root():
    return redirect(url_for('index'))

@app.route("/")
def index():
    return render_template("index.html")

# --- INTELLIGENCE HELPERS ---
def get_git_info(path):
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                         cwd=path, stderr=subprocess.STDOUT).decode("utf-8").strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], 
                                         cwd=path, stderr=subprocess.STDOUT).decode("utf-8").strip()
        dirty_count = len([l for l in dirty.split("\n") if l])
        return {"branch": branch, "dirty": dirty_count, "is_git": True}
    except Exception:
        return {"branch": "DEV", "dirty": 0, "is_git": False}

def detect_dna(path):
    indicators = {
        "Python": "**/*.py",
        "JavaScript": "**/*.js",
        "React": "**/*.jsx",
        "TypeScript": "**/*.ts",
        "HTML": "**/*.html",
        "Shell": "**/*.sh"
    }
    dna = {}
    for lang, pattern in indicators.items():
        count = len(glob.glob(os.path.join(path, pattern), recursive=True))
        if count > 0: dna[lang] = count
    return dna

# --- NEW API: CHRONICLE (Timeline) ---
@app.route("/api/timeline")
def get_timeline():
    try:
        # Get 20 most recently modified files across all projects
        cmd = ["find", WORKSPACE_ROOT, "-not", "-path", "*/.*", "-type", "f", "-mtime", "-2", "-print0"]
        files = subprocess.check_output(cmd).decode("utf-8", errors="ignore").split("\x00")
        
        file_details = []
        for f in files:
            if f and os.path.exists(f) and "node_modules" not in f and "cache" not in f:
                file_details.append({
                    "name": os.path.basename(f),
                    "path": f.replace(WORKSPACE_ROOT, ""),
                    "project": f.replace(WORKSPACE_ROOT + "/", "").split("/")[0],
                    "time": os.path.getmtime(f)
                })
        
        # Sort by time desc
        file_details.sort(key=lambda x: x["time"], reverse=True)
        return jsonify(file_details[:20])
    except Exception as e:
        return jsonify({"error": str(e)})

# --- NEW API: ORCHESTRA (Automations) ---
@app.route("/api/automate", methods=["POST"])
def automate():
    action = request.json.get("action")
    target = request.json.get("target", "all") # "all" or project name
    
    results = []
    
    if action == "sync":
        # Run git fetch across all projects
        for item in os.listdir(WORKSPACE_ROOT):
            p_path = os.path.join(WORKSPACE_ROOT, item)
            if os.path.isdir(p_path) and os.path.exists(os.path.join(p_path, ".git")):
                try:
                    subprocess.run(["git", "fetch", "--all"], cwd=p_path, timeout=5)
                    results.append({"project": item, "status": "Synced"})
                except Exception:
                    results.append({"project": item, "status": "Failed"})
        return jsonify({"message": "Orchestral Sync Complete", "results": results})

    if action == "cleanup":
        # Identify node_modules and cache folders
        total_freed = 0
        for item in os.listdir(WORKSPACE_ROOT):
            p_path = os.path.join(WORKSPACE_ROOT, item)
            if os.path.isdir(p_path):
                # We won't actually delete node_modules in this MVP, but we'll clear __pycache__ and .next
                targets = [f"{p_path}/**/__pycache__", f"{p_path}/**/.next/cache", f"{p_path}/**/*.pyc"]
                for t in targets:
                    for found in glob.glob(t, recursive=True):
                        try:
                            size = os.path.getsize(found)
                            if os.path.isdir(found): shutil.rmtree(found)
                            else: os.remove(found)
                            total_freed += size
                        except Exception: pass
        return jsonify({"message": f"Housekeeping Complete. Freed {total_freed // 1024} KB."})

    return jsonify({"error": "Unknown protocol"}), 400

# --- NEW API: STATS (Intelligence) ---
@app.route("/api/workspace_stats")
def workspace_stats():
    total_loc = 0
    lang_distribution = {"Python": 0, "JS/TS": 0, "HTML/CSS": 0, "Other": 0}
    
    # Fast estimation of workspace DNA
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        if ".git" in root or "node_modules" in root: continue
        for f in files:
            ext = f.split(".")[-1]
            if ext == "py": lang_distribution["Python"] += 1
            elif ext in ["js", "jsx", "ts", "tsx"]: lang_distribution["JS/TS"] += 1
            elif ext in ["html", "css"]: lang_distribution["HTML/CSS"] += 1
            else: lang_distribution["Other"] += 1
            
    total_found = sum(lang_distribution.values())
    return jsonify({
        "dna": lang_distribution,
        "dna_total": total_found or 1,
        "project_count": len([i for i in os.listdir(WORKSPACE_ROOT) if os.path.isdir(os.path.join(WORKSPACE_ROOT, i)) and not i.startswith(".")]),
        "disk_root": psutil.disk_usage("/").percent
    })

# --- EXISTING CORE ---
def get_project_health(path, git_info):
    # Optimized scanner: EXCLUDE node_modules, .git, and build folders
    try:
        cmd = f"grep -rIE --exclude-dir={{node_modules,.git,.next,__pycache__}} 'TODO|FIXME' {path} | wc -l"
        todo_count = int(subprocess.check_output(cmd, shell=True, timeout=2).decode().strip())
    except Exception: todo_count = 0
    
    dirty = git_info.get("dirty", 0)
    if dirty == 0 and todo_count == 0: return "stable" # Green
    if dirty < 5 and todo_count < 2: return "active" # Yellow
    if dirty < 15 and todo_count < 10: return "dirty" # Orange
    return "critical" # Red

@app.route("/api/projects")
def list_projects():
    projects = []
    for item in os.listdir(WORKSPACE_ROOT):
        p_path = os.path.join(WORKSPACE_ROOT, item)
        if os.path.isdir(p_path) and not item.startswith("."):
            git = get_git_info(p_path)
            projects.append({
                "name": item, "path": p_path, 
                "git": git,
                "health": get_project_health(p_path, git),
                "last_mod": time.ctime(os.path.getmtime(p_path))
            })
    return jsonify(projects)

@app.route("/api/todos")
def get_todos():
    try:
        # Optimized scrape of TODO/FIXME across all projects
        cmd = f"grep -rnIE --exclude-dir={{node_modules,.git,.next,__pycache__}} 'TODO|FIXME|HACK' {WORKSPACE_ROOT} | head -n 50"
        output = subprocess.check_output(cmd, shell=True, timeout=5).decode("utf-8")
        todos = []
        for line in output.split("\n"):
            if ":" in line:
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    # Clean up project name from path
                    proj = parts[0].replace(WORKSPACE_ROOT + "/", "").split("/")[0]
                    todos.append({"project": proj, "text": parts[3].strip(), "file": parts[0]})
        return jsonify(todos)
    except Exception:
        return jsonify([])

@app.route("/api/search")
def search():
    query = request.args.get("q")
    try:
        cmd = ["grep", "-rnI", "--exclude-dir=.git", "--exclude-dir=node_modules", query, WORKSPACE_ROOT]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
        results = [{"file": l.split(":")[0], "line": l.split(":")[1], "content": l.split(":", 2)[2].strip()} for l in output.split("\n")[:20] if ":" in l]
        return jsonify(results)
    except Exception: return jsonify([])

@app.route("/api/launch", methods=["POST"])
def launch():
    data = request.json
    p, target, l = data.get("path"), data.get("target"), data.get("line", "")
    if target == "vscode": subprocess.Popen(["code", "-g", f"{p}:{l}" if l else p])
    elif target == "antigravity": subprocess.Popen(["open", "-a", "Antigravity", "--args", p])
    elif target == "terminal": subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script "cd {p}"'])
    return jsonify({"status": "success", "message": f"Launched {target}"})

@app.route("/api/metrics")
def metrics():
    return jsonify({"cpu": psutil.cpu_percent(), "mem": psutil.virtual_memory().percent, "uptime": str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9911, debug=True)
