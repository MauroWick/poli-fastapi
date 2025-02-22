from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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

@app.get("/alunos/{aluno_id}", response_model=Aluno)
async def get_aluno(aluno_id: int):
    fake_aluno = Aluno(
        nome="John Doe",
        email="johndoe@example.com",
        universidade="Universidade Exemplo",
        curso=1,
        ano_graduacao=2024,
        telefone="123456789",
        cidade="Cidade Exemplo",
        estado="Estado Exemplo",
        pais="Pais Exemplo",
        cpf="12345678900",
        modalidade_estagio="Remoto",
        competencias=["Python", "FastAPI"],
        ja_estagiou=True,
        autoriza_dados=True
    )
    return fake_aluno

@app.get("/alunos", response_model=list[Aluno])
async def get_alunos():
    fake_alunos = [
        Aluno(
            nome=f"John Doe {i}",
            email=f"johndoe{i}@example.com",
            universidade="Universidade Exemplo",
            curso=1,
            ano_graduacao=2024,
            telefone=f"12345678{i}",
            cidade="Cidade Exemplo",
            estado="Estado Exemplo",
            pais="Pais Exemplo",
            cpf=f"1234567890{i}",
            modalidade_estagio="Remoto",
            competencias=["Python", "FastAPI"],
            ja_estagiou=True,
            autoriza_dados=True
        ) for i in range(10)
    ]
    return fake_alunos