from .models import Aluno

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
