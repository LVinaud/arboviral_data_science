"""Smoke tests: garantem que o pacote é importável e o esquema é válido."""
import yaml

import arboviral
from arboviral.io import CONFIGS


def test_package_importavel():
    assert arboviral.__version__


def test_schema_yaml_valido():
    with open(CONFIGS / "schema.yaml", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert "chaves" in schema
    assert {"cod_ibge", "ano", "mes"} <= set(schema["chaves"].keys())


def test_municipios_poc_tem_32():
    with open(CONFIGS / "municipios_poc.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert len(cfg["municipios"]) == 32
