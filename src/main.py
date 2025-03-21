import json
import io
import re

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum
import pandas as pd

from fake_alunos import FAKE_ALUNOS


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Aluno(BaseModel):
    nome: str
    email: str
    universidade: str
    curso: str
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
    return FAKE_ALUNOS[0]


@app.get("/alunos", response_model=list[Aluno])
async def get_alunos():
    return FAKE_ALUNOS


@app.get("/university")
def get_universities():
    return {
    'universities': list({aluno['universidade'] for aluno in FAKE_ALUNOS})
    }


@app.get("/course")
def get_courses():
    return {
    'courses': list({aluno['curso'] for aluno in FAKE_ALUNOS})
    }


@app.get("/skill")
def get_skills():
    skills = []
    for aluno in FAKE_ALUNOS:
        skills.extend(aluno['competencias'])
    return {
        'skills': skills
    }


@app.get("/filter_options")
def get_filter_options():
    return {
        'universities': list({aluno['universidade'] for aluno in FAKE_ALUNOS}),
        'courses': list({aluno['curso'] for aluno in FAKE_ALUNOS}),
        'skills': list({skill for aluno in FAKE_ALUNOS for skill in aluno['competencias']})
    }


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
