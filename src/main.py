import io
import re
import logging

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from mangum import Mangum

app = FastAPI(
    title="Poli-API",
    description="API para upload e processamento de planilhas de alunos.",
    version="1.0.0",
    openapi_url="/swagger.json"
)

REQUIRED_COLUMNS = [
    "Nome",
    "Email de contato",
    "Universidade",
    "Curso",
    "Ano de graduação",
    "Telefone",
    "Cidade",
    "Estado",
    "País",
    "CPF (só números)",
    "Modalidades de estágio buscadas",
    "Competências",
    "Já estagiou?/ Está estagiando?",
    "Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?"
]

ALL_COLUMNS = [
    "Nome",
    "Email de contato",
    "Universidade",
    "Curso",
    "Ano de graduação",
    "Telefone",
    "Cidade",
    "Estado",
    "País",
    "CPF (só números)",
    "Modalidades de estágio buscadas",
    "Competências",
    "Já estagiou?/ Está estagiando?",
    "Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?",
    "Email institucional",
    "Aberto a propostas de trabalho",
    "Áreas de interesse",
    "Organizações estudantis",
    "LinkedIn",
    "Currículo",
    "Etnia",
    "Gênero",
    "PCD",
    "LGBTQIA+",
    "Data de nascimento (DD/MM/AA)",
    "Ano de ingresso na universidade",
    "Previsão Formatura",
    "Nível de Espanhol",
    "Nível de Inglês",
    "Nível de Excel",
    "Setores de Interesse",
    "Qual é a primeira empresa que vem à sua mente quando pensa em estagiar?",
    "Caso tenha outras competências, indique quais",
    "Se sim, em qual setor(es)?"
]

COLUMN_MAPPING = {
    "Nome": "nome",
    "Email de contato": "email",
    "Universidade": "universidade",
    "Curso": "curso",
    "Ano de graduação": "ano_graduacao",
    "Telefone": "telefone",
    "Cidade": "cidade",
    "Estado": "estado",
    "País": "pais",
    "CPF (só números)": "cpf",
    "Modalidades de estágio buscadas": "modalidade_estagio",
    "Competências": "competencias",
    "Já estagiou?/ Está estagiando?": "ja_estagiou",
    "Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?": "autoriza_dados"
}


# CONFIGURAÇÃO DO LOGGER
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fastapi_lambda")


class Aluno(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr
    universidade: str
    curso: str
    ano_graduacao: int = Field(..., ge=1900, le=2100)
    telefone: str = Field(..., pattern=r"^\(\d{2}\)\s?\d{5}-\d{4}$")
    cidade: str
    estado: str
    pais: str
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
    modalidade_estagio: list[str]
    competencias: list[str]
    ja_estagiou: bool
    autoriza_dados: bool

    @field_validator("nome", "universidade", "cidade", "estado", "pais")
    @classmethod
    def validar_texto(cls, v):
        if re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", v):
            return v
        raise ValueError("Deve conter apenas letras e espaços")

    @field_validator("modalidade_estagio", mode="before")
    @classmethod
    def split_modalidade(cls, v):
        if isinstance(v, str):
            items = [item.strip() for item in v.split(",") if item.strip()]
            if len(items) > 10:
                raise ValueError("Modalidade de Estágio Buscada deve conter no máximo 10 itens")
            if not all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", item) for item in items):
                raise ValueError("Cada item de Modalidade de Estágio Buscada deve conter apenas letras e espaços")
            return items
        return v

    @field_validator("competencias", mode="before")
    @classmethod
    def split_competencias(cls, v):
        return [comp.strip() for comp in re.split(r'[;,]', v) if comp.strip()] if isinstance(v, str) else v

    @field_validator("competencias")
    @classmethod
    def validar_competencias(cls, v):
        if not isinstance(v, list):
            raise ValueError("Competências deve ser uma lista")
        if len(v) > 100:
            raise ValueError("Competências deve conter no máximo 100 itens")
        if not all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", comp) for comp in v):
            raise ValueError("Cada competência deve conter apenas letras e espaços")
        return v

    @field_validator("ja_estagiou", mode="before")
    @classmethod
    def parse_ja_estagiou(cls, v):
        return v if isinstance(v, bool) else (
            True if isinstance(v, str) and v.strip().lower() == "sim" else
            False if isinstance(v, str) and v.strip().lower() == "não" else
            (_ for _ in ()).throw(ValueError("Valor inválido para ja_estagiou, use 'Sim' ou 'Não'"))
        )

    @field_validator("autoriza_dados", mode="before")
    @classmethod
    def parse_autoriza_dados(cls, v):
        return v if isinstance(v, bool) else (
            True if isinstance(v, str) and v.strip().lower() == "sim" else
            False if isinstance(v, str) and v.strip().lower() == "não" else
            (_ for _ in ()).throw(ValueError("Valor inválido para autoriza_dados, use 'Sim' ou 'Não'"))
        )

def process_spreadsheet(spreadsheet: bytes):
    try:
        df = pd.read_excel(io.BytesIO(spreadsheet))
        df = df[[col for col in ALL_COLUMNS if col in df.columns]]

        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            return JSONResponse(
                content={
                    "status": "erro",
                    "erros": {"Geral": [f"Colunas obrigatórias ausentes: {missing_cols}"]}
                },
                status_code=400,
            )

        criticas = {}
        valid_alunos = []

        for index, row in df.iterrows():
            cpf_val = row.get("CPF (só números)") if pd.notnull(row.get("CPF (só números)")) else "cpf não localizado"
            nome_val = row.get("Nome") if pd.notnull(row.get("Nome")) else "nome não localizado"
            key = f"{cpf_val}: {nome_val}"

            row_errors = [f"Campo obrigatório '{col}' está vazio." for col in REQUIRED_COLUMNS if pd.isnull(row.get(col))]
            if row_errors:
                criticas[key] = row_errors
                continue

            data = {model_field: row[excel_field] for excel_field, model_field in COLUMN_MAPPING.items() if excel_field in row}

            try:
                aluno = Aluno(**data)
                valid_alunos.append(aluno.dict())
            except Exception as exc:
                criticas[key] = [f"Erro de validação: {exc.errors()}"]

        unique_fields = ["Nome", "Email de contato", "Telefone", "CPF (só números)"]
        for field in unique_fields:
            duplicates = df[df.duplicated(subset=[field], keep=False)]
            for idx, dup_row in duplicates.iterrows():
                value = dup_row.get(field)
                if pd.notnull(value):
                    cpf_dup = dup_row.get("CPF (só números)") if pd.notnull(dup_row.get("CPF (só números)")) else "cpf não localizado"
                    nome_dup = dup_row.get("Nome") if pd.notnull(dup_row.get("Nome")) else "nome não localizado"
                    key_dup = f"{cpf_dup}: {nome_dup}"
                    msg = f"Campo único '{field}' possui valor duplicado: {value}."
                    criticas.setdefault(key_dup, [])
                    if msg not in criticas[key_dup]:
                        criticas[key_dup].append(msg)

        if criticas:
            logger.error("Criticas encontradas na planilha.")
            return JSONResponse(content={"status": "criticas", "erros": criticas}, status_code=400)

        logger.info("Planilha processada com sucesso.")
        return JSONResponse(content={"status": "sucess", "data": valid_alunos}, status_code=200)

    except Exception as e:
        logger.error(f"Erro ao processar a planilha: {e}")
        raise HTTPException(status_code=500, detail="Erro no processamento da planilha.")


fake_aluno = Aluno(
    nome="John Doe",
    email="johndoe@example.com",
    universidade="UniversidadeExemplo",
    curso="CursoExemplo",
    ano_graduacao=2024,
    telefone="(11)91234-5678",
    cidade="CidadeExemplo",
    estado="EstadoExemplo",
    pais="PaisExemplo",
    cpf="123.456.789-00",
    modalidade_estagio=["Remoto"],
    competencias=["Python", "FastAPI"],
    ja_estagiou=True,
    autoriza_dados=True
)

fake_alunos = [
    Aluno(
        nome=f"John Doe {chr(65+i)}",
        email=f"johndoe{i}@example.com",
        universidade="UniversidadeExemplo",
        curso=f"Curso{i}Exemplo",
        ano_graduacao=2024,
        telefone=f"(11)91234-56{78 + i:02d}",
        cidade="CidadeExemplo",
        estado="EstadoExemplo",
        pais="PaisExemplo",
        cpf=f"123.456.789-{i:02d}",
        modalidade_estagio=["Remoto"],
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
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um .xlsx")
    try:
        contents = await file.read()
        result = process_spreadsheet(contents)
        return result
    except Exception as e:
        logger.error(f"Erro ao processar a planilha: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
lambda_handler = Mangum(app)


# http://localhost:8000/docs (para acessar o swagger em sua maquina local)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)