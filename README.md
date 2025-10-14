# Medifolder

Boilerplate simples para iniciar um projeto Python seguindo o layout `src/`.

## Estrutura

```
.
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── medifolder/
│       ├── __main__.py
│       └── __init__.py
└── tests/
    └── test_example.py
```

## Como usar

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Instale dependências de desenvolvimento:
   ```bash
   pip install -e .[dev]
   ```
3. Execute os testes:
   ```bash
   pytest
   ```

## Scripts úteis

```bash
python -m medifolder  # roda o entrypoint principal
```

## Próximos passos

- Ajuste os campos em `pyproject.toml` conforme o seu projeto.
- Crie módulos adicionais dentro de `src/medifolder`.
- Adicione novos testes em `tests/`.
