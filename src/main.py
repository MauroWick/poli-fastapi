import io
import re
import logging

import boto3
import pandas as pd
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from mangum import Mangum

dynamodb = boto3.client("dynamodb", region_name="us-east-1")

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
    "Email institucional",
    "Universidade",
    "Curso",
    "Ano de graduação",
    "Aberto a propostas de trabalho",
    "Áreas de interesse",
    "Telefone",
    "Cidade",
    "Estado",
    "País",
    "CPF (só números)",
    "Modalidades de estágio buscadas",
    "Competências",
    "Já estagiou?/ Está estagiando?",
    "Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?",
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
    "Email institucional": "email_institucional",
    "Universidade": "universidade",
    "Curso": "curso",
    "Ano de graduação": "ano_graduacao",
    "Aberto a propostas de trabalho": "aberto_proposta_trabalho",
    "Áreas de interesse": "areas_interesse",
    "Telefone": "telefone",
    "Etnia": "etnia",
    "PCD": "pcd",
    "LGBTQIA+": "lgbtqia",
    "Cidade": "cidade",
    "Estado": "estado",
    "País": "pais",
    "Data de nascimento (DD/MM/AA)": "data_nascimento",
    "CPF (só números)": "cpf",
    "Ano de ingresso na universidade": "ano_ingresso",
    "Previsão Formatura": "previsao_formatura",
    "Nível de Espanhol": "nivel_espanhol",
    "Nível de Inglês": "nivel_ingles",
    "Nível de Excel": "nivel_excel",
    "Setores de Interesse": "setores_interesse",
    "Modalidades de estágio buscadas": "modalidade_estagio",
    "Qual é a primeira empresa que vem à sua mente quando pensa em estagiar?": "primeira_empresa",
    "Competências": "competencias",
    "Caso tenha outras competências, indique quais": "outras_competencias",
    "Já estagiou?/ Está estagiando?": "ja_estagiou",
    "Se sim, em qual setor?": "se_sim_setor",
    "Você autoriza o compartilhamento dos seus dados para os bancos de talentos das empresas presentes no WI34?": "autoriza_dados"
}


# CONFIGURAÇÃO DO LOGGER
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fastapi_lambda")


class Aluno(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=50)
    email_institucional: Optional[EmailStr] = Field(None, max_length=50)
    universidade: str
    curso: str
    ano_graduacao: int = Field(..., ge=1900, le=2100)
    aberto_proposta_trabalho: Optional[str] = None
    areas_interesse: Optional[List[str]] = None
    organizacoes_estudantis: Optional[List[str]] = None
    telefone: str = Field(..., pattern=r"^\(\d{2}\)\s?\d{5}-\d{4}$")
    etnia: Optional[str] = None
    lgbtqia: Optional[str] = None
    pcd: Optional[str] = None
    cidade: str
    estado: str
    pais: str
    data_nascimento: Optional[str] = None
    cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
    ano_ingresso: Optional[int] = None
    previsao_formatura: Optional[str] = None
    nivel_espanhol: Optional[str] = None
    nivel_ingles: Optional[str] = None
    nivel_excel: Optional[str] = None
    setores_interesse: Optional[List[str]] = None
    modalidade_estagio: list[str]
    primeira_empresa: Optional[str] = None
    competencias: list[str]
    outras_competencias: Optional[List[str]] = None
    ja_estagiou: bool
    se_sim_setor: Optional[str] = None
    autoriza_dados: bool

    @field_validator("nome", "universidade", "curso", "etnia", "pcd", "lgbtqia", "cidade", "estado", "pais", "nivel_espanhol", "nivel_ingles", "nivel_excel", "primeira_empresa", "se_sim_setor")
    @classmethod
    def validar_texto(cls, v):
        if not isinstance(v, str):
            v = str(v) if v is not None else ""
        if re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", v):
            return v
        raise ValueError("Deve conter apenas letras e espaços")
    
    @field_validator("email", "email_institucional", mode="before")
    @classmethod
    def validate_local_part(cls, v: str):
        local_part = v.split("@")[0]
        if len(local_part) > 50:
            raise ValueError("A parte local do email de contato deve ter no máximo 50 caracteres")
        return v

    @field_validator("aberto_proposta_trabalho", mode="before")
    @classmethod
    def validate_aberto_proposta_trabalho(cls, v):
        if v is None:
            return v
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", v):
            raise ValueError("Deve conter apenas letras e espaços")
        if v.strip().lower() not in {"sim", "não"}:
            raise ValueError("Valor inválido, use 'Sim' ou 'Não'")
        return v
    
    @field_validator("areas_interesse", mode="before")
    @classmethod
    def split_areas_interesse(cls, v):
        if isinstance(v, str):
            items = [item.strip() for item in re.split(r"[;,]", v) if item.strip()]
            if len(items) > 100:
                raise ValueError("Áreas de Interesse deve conter no máximo 100 itens")
            return items
        return v
    
    @field_validator("organizacoes_estudantis", mode="before")
    @classmethod
    def split_organizacoes_estudantis(cls, v):
        if isinstance(v, str):
            items = [item.strip() for item in re.split(r"[;,]", v) if item.strip()]
            if not all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", item) for item in items):
                raise ValueError("Cada item de Organizações estudantis deve conter apenas letras e espaços")
            return items
        return v
    
    @field_validator("data_nascimento", mode="before")
    @classmethod
    def validate_data_nascimento(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("Data de nascimento deve ser uma string")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("Data de nascimento deve estar no formato AAAA-MM-DD")
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            raise ValueError("Data de nascimento inválida")
        return v
    
    @field_validator("setores_interesse", mode="before")
    @classmethod
    def split_setores_interesse(cls, v):
        if isinstance(v, str):
            items = [item.strip() for item in re.split(r"[;,]", v) if item.strip()]
            if len(items) > 100:
                raise ValueError("Setores de Interesse deve conter no máximo 100 itens")
            if not all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s]+", item) for item in items):
                raise ValueError("Cada setor de interesse deve conter apenas letras e espaços")
            return items
        return v
    
    @field_validator("previsao_formatura", mode="before")
    @classmethod
    def validate_previsao_formatura(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            v = str(v)
        if not re.fullmatch(r"\d{4}\.\d", v):
            raise ValueError("Previsão de Formatura deve estar no formato YYYY.X, ex: 2024.1")
        return v

    
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
        if not isinstance(v, str):
            return None
        return [comp.strip() for comp in re.split(r'[;,]', v) if comp.strip()]

    @field_validator("outras_competencias", mode="before")
    @classmethod
    def split_outras_competencias(cls, v):
        if isinstance(v, str):
            items = [comp.strip() for comp in re.split(r"[;,]", v) if comp.strip()]
            if len(items) > 100:
                raise ValueError("Outras Competências deve conter no máximo 100 itens")
            return items
        return v
    
    @field_validator("competencias", "outras_competencias")
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
        df.fillna("", inplace=True)
        colunas_texto = ["Nome", "Email de contato", "Email institucional", "Universidade", "Curso",
                  "Aberto a propostas de trabalho", "Áreas de interesse", "Telefone", "Etnia", "PCD", 
                  "LGBTQIA+", "Cidade", "Estado", "País", "Data de nascimento (DD/MM/AA)", 
                  "CPF (só números)", "Previsão Formatura", "Nível de Espanhol", "Nível de Inglês", 
                  "Nível de Excel", "Setores de Interesse", "Qual é a primeira empresa que vem à sua mente quando pensa em estagiar?", 
                  "Competências", "Caso tenha outras competências, indique quais", "Já estagiou?/ Está estagiando?", "Se sim, em qual setor?"]
        for col in colunas_texto:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if pd.notnull(x) else None)

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
                if hasattr(exc, "errors"):
                    criticas[key] = [f"Erro de validação: {exc.errors()}"]
                else:
                    criticas[key] = [f"Erro de validação: {str(exc)}"]

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


@app.get("/alunos/{cpf}")
async def get_aluno(cpf: str):
    item = dynamodb.get_item(
        TableName="poli_fastapi_table_students", 
        Key={"cpf": {"S": cpf}}
    )
    if item.get("Item"):
        return {"message": f"Aluno {item["Item"]["cpf"]} encontrado com sucesso!"}
    else:
        return {"message": "Aluno não encontrado!"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)