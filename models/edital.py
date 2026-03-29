import hashlib
from datetime import datetime
from pydantic import BaseModel, computed_field

class Edital(BaseModel):
    titulo: str
    orgao: str
    objetivo: str | None = None
    publico_alvo: list[str] = []
    areas_tematicas: list[str] = []
    elegibilidade: str | None = None 
    prazo_submissao: str | None = None
    valor_financiamento: str | None = None
    modalidade_fomento: str | None = None
    documentos_exigidos: list[str] = []
    criterios_avaliacao: str | None = None
    cronograma: list[dict] = []
    link_edital: str
    link_pdf_principal: str | None = None
    links_anexos: list[str] = []
    observacoes: str | None = None
    fonte: str 
    extraido_em: datetime

    @computed_field
    @property
    def id(self) -> str:
        return hashlib.sha256(self.link_edital.encode()).hexdigest()[:12]