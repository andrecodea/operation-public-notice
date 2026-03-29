"""Tests Edital BaseModel configs and computed fields"""

from datetime import datetime
from models.edital import Edital

def _minimal_notice():
    return {
        "titulo": "Edital de Pesquisa 2026",
        "orgao": "FAPDF",
        "link_edital": "https://fap.df.gov.br/edital/1",
        "fonte": "fapdf",
        "extraido_em": datetime.now().isoformat()
    }

def test_edital_id_and_deterministic():
    data = _minimal_notice()
    notice1 = Edital.model_validate(data)
    notice2 = Edital.model_validate(data)
    assert notice1.id == notice2.id

def test_edital_id_changes_with_diff_link():
    data1 = {**_minimal_notice(), "link_edital": "https://fap.df.gov.br/edital/1"}
    data2 = {**_minimal_notice(), "link_edital": "https://fap.df.gov.br/edital/2"}
    assert Edital.model_validate(data1).id != Edital.model_validate(data2).id

def test_if_edital_has_12_chars():
    notice = Edital.model_validate(_minimal_notice())
    assert len(notice.id) == 12

def test_optional_fields_default_none():
    notice = Edital.model_validate(_minimal_notice())
    assert notice.objetivo is None
    assert notice.prazo_submissao is None
    assert notice.valor_financiamento is None

def test_fields_list_default_empty():
    notice = Edital.model_validate(_minimal_notice())
    assert notice.publico_alvo == []
    assert notice.areas_tematicas == []
    assert notice.documentos_exigidos == []

def test_id_doesnt_show_in_llm_prompt():
    # id is computed_field, must not be in model_fields
    assert "id" not in Edital.model_fields
