"""Testa o BaseModel e as configs do Edital"""

from datetime import datetime
from models.edital import Edital

def _minimal_edital():
    return {
        "titulo": "Edital de Pesquisa 2026",
        "orgao": "FAPDF",
        "link_edital": "https://fap.df.gov.br/edital/1",
        "fonte": "fapdf",
        "extraido_em": datetime.now().isoformat()
    }

def test_edital_id_and_deterministic():
    data = _minimal_edital()
    edital1 = Edital.model_validate(data)
    edital2 = Edital.model_validate(data)
    assert edital1.id == edital2.id

def test_edital_id_changes_with_diff_link():
    data1 = {**_minimal_edital(), "link_edital": "https;//fap.df.gov.br/edital/1"}
    data2 = {**_minimal_edital(), "link_edital": "https;//fap.df.gov.br/edital/2"}
    assert Edital.model_validate(data1) != Edital.model_validate(data2)

def test_if_edital_has_12_chars():
    edital = Edital.model_validate(_minimal_edital())
    assert len(edital.id) == 12

def test_optional_fields_default_none():
    edital = Edital.model_validate(_minimal_edital())
    assert edital.objetivo is None
    assert edital.prazo_submissão is None
    assert edital.valor_financiamento is None

def test_fields_list_default_empty():
    edital = Edital.model_validate(_minimal_edital())
    assert edital.publico_alvo == []
    assert edital.areas_tematicas == []
    assert edital.documentos_exigidos == []

def test_id_doesnt_show_in_llms_prompt():
    # id is computed_field, must not be in model_fields fields
    assert "id" not in Edital.model_fields
