from pydantic import BaseModel, HttpUrl

class Aluno(BaseModel):
    nome: str
    email: str
    universidade: str
    curso: int
    ano_graduacao: int
    telefone: str
    cidade: str
    estado: str
    pais: str
    cpf: str
    modalidade_estagio: str
    competencias: list
    ja_estagiou: bool
    autoriza_dados: bool

class SpreadsheetLink(BaseModel):
    url: HttpUrl
