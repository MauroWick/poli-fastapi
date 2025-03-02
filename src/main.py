import json
import io
import re

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from mangum import Mangum
import pandas as pd


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


@app.get("/alunos/{aluno_id}", response_model=Aluno)
async def get_aluno(aluno_id: int):
    return fake_aluno


@app.get("/alunos", response_model=list[Aluno])
async def get_alunos():
    return fake_alunos


@app.post("/upload_spreadsheet")
async def upload_spreadsheet(file: UploadFile = File(...)):
    contents = await file.read()

    if not re.match(r".*\.xlsx$", file.filename):
        return HTTPException(status_code=400, detail="Arquivo deve ser um .xlsx")
    elif not file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return HTTPException(status_code=400, detail="Arquivo deve ser um .xlsx") 

    try:
        json_data = _spreadsheet_to_json(contents)
        return json_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _check_required_columns(df):
    REQUIRED_COLUMNS = [
        'Nome',
        'Email de contato',
        'Universidade',
        'Curso',
        'Ano de graduação',
        'Telefone',
        'Cidade',
        'Estado',
        'País',
        'CPF (só números)',
        'Modalidades de estágio buscadas',
        'Competências',
        'Já estagiou?/ Está estagiando?',
        'Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?',
    ]

    cols = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            cols.append(col)

    if len(cols) > 0:
        raise HTTPException(status_code=500, detail=f"Colunas {cols} não encontrada")


def _spreadsheet_to_json(spreadsheet):

    ALL_COLUMNS = [
        'Nome',
        'Email de contato',
        'Universidade',
        'Curso',
        'Ano de graduação',
        'Telefone',
        'Cidade',
        'Estado',
        'País',
        'CPF (só números)',
        'Modalidades de estágio buscadas',
        'Competências',
        'Já estagiou?/ Está estagiando?',
        'Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?',
        'Email institucional',
        'Aberto a propostas de trabalho',
        'Áreas de interesse',
        'Organizações estudantis',
        'LinkedIn',
        'Currículo',
        'Etnia',
        'Gênero',
        'PCD',
        'LGBTQIA+',
        'Data de nascimento (DD/MM/AA)',
        'Ano de ingresso na universidade',
        'Previsão Formatura',
        'Nível de Espanhol',
        'Nível de Inglês',
        'Nível de Excel',
        'Setores de Interesse',
        'Qual é a primeira empresa que vem a sua mente quando pensa em estagiar?',
        'Caso tenha outras competências, indique quais',
        'Se sim, em qual setor(es)?',
    ]

    df = pd.read_excel(io.BytesIO(spreadsheet), usecols=ALL_COLUMNS)
    _check_required_columns(df)

    json_str = df.to_json(orient='records')
    json_data = json.loads(json_str)
    return json_data
    

lambda_handler = Mangum(app)
