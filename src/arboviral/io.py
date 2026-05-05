"""Caminhos canônicos do projeto.

Use estas constantes em todos os módulos para evitar caminhos hardcoded.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
MANUAL = DATA / "manual"
LOOKUP = DATA / "lookup"
CONFIGS = ROOT / "configs"
