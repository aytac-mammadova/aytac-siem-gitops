#!/usr/bin/env python3
"""
deploy_qradar.py - Sigma YAML (qradar_rules/) -> AQL generasiya + QRadar API yoxlama.
QRadar offense rule-lari resmi API ile sifirdan yaradilmadigi ucun, bu skript
her YAML-i AQL-e cevirir (qradar_rules/generated_aql/ icine yazir). Bu AQL-ler
QRadar Rule Wizard-da offense qurmaq ucun istifade olunur.
"""
import os, glob, subprocess, urllib3, requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

QRADAR_HOST  = os.environ.get("QRADAR_HOST", "").rstrip("/")
QRADAR_TOKEN = os.environ.get("QRADAR_TOKEN", "")
RULES_DIR    = os.environ.get("RULES_DIR", "qradar_rules")
OUT_DIR      = os.path.join(RULES_DIR, "generated_aql")
PIPELINE     = ["-p", "qradar-aql-payload"]


def to_aql(path):
    cmd = ["sigma", "convert", "-t", "q_radar_aql"] + PIPELINE + [path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return "\n".join(l for l in r.stdout.splitlines()
                     if l.strip() and "Parsing Sigma" not in l).strip()


def generate_all():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RULES_DIR, "*.yml")))
    print(f"{len(files)} QRadar qaydasi AQL-e cevrilir...\n")
    for f in files:
        try:
            aql = to_aql(f)
            out = os.path.join(OUT_DIR, os.path.splitext(os.path.basename(f))[0] + ".aql")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(aql + "\n")
            print(f"[AQL] {os.path.basename(out)}")
        except Exception as e:
            print(f"[ERROR] {os.path.basename(f)}: {e}")


def test_api():
    if not QRADAR_HOST or not QRADAR_TOKEN:
        print("\n[INFO] QRADAR_HOST/QRADAR_TOKEN teyin edilmeyib - API yoxlamasi atlanildi.")
        return
    h = {"SEC": QRADAR_TOKEN, "Version": "16.0", "Accept": "application/json"}
    try:
        r = requests.get(f"{QRADAR_HOST}/api/system/about", headers=h, verify=False, timeout=15)
        print(f"\n[API] QRadar elaqe statusu: {r.status_code}")
    except Exception as e:
        print(f"\n[API] QRadar elaqe xetasi: {e}")


if __name__ == "__main__":
    generate_all()
    test_api()
