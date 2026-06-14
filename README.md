# PowerTrace

MVP web para geração e dimensionamento acadêmico de plantas elétricas
residenciais, com API FastAPI, arquivos DXF e frontend React em português.

## Executar o backend

```powershell
cd backend
python -m pip install -e .
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Configure antes o arquivo `backend/.env` a partir de `.env.example`.
A API ficará disponível em `http://127.0.0.1:8000` e o Swagger em
`http://127.0.0.1:8000/docs`.

## Executar o frontend

```powershell
cd frontend
npm install
npm run dev
```

Configure `frontend/.env` quando a API não estiver em
`http://127.0.0.1:8000`. A aplicação ficará disponível em
`http://127.0.0.1:5173`.

## Fluxo do MVP

1. Cadastrar uma conta e entrar.
2. Criar e abrir um projeto.
3. Gerar uma planta informando largura, comprimento e seed opcional.
4. Consultar cômodos, cargas e circuitos dimensionados.
5. Personalizar TUEs e regenerar a planta com a mesma seed.
6. Baixar o DXF autenticado.

O dimensionamento gerado é acadêmico e preliminar. Uma instalação real
requer projeto e validação de profissional habilitado.
