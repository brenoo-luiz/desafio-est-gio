# Minha Solução — Banco

## Stack
- **Backend:** Python 3.11+ com [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- **Frontend:** HTML/CSS/JavaScript puro (sem framework, sem build step)

## Pré-requisitos / dependências
- Python 3.11 ou superior instalado (`python3 --version`)
- Não é necessário Node, banco de dados ou qualquer outra ferramenta — as contas
  vivem em memória no processo do backend (ver seção **Observações**).

## Como executar

### Backend (API)

```bash
cd backend
python3 -m venv venv

# Linux/macOS
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

A API sobe em **http://localhost:8000**. Documentação interativa (Swagger) em
**http://localhost:8000/docs**.

### Frontend

Em outro terminal (com o backend já rodando), a partir da raiz do projeto:

```bash
cd frontend
python3 -m http.server 5500
```

Abra **http://localhost:5500** no navegador.

> O frontend é HTML/CSS/JS puro — qualquer servidor estático funciona
> (`python3 -m http.server`, extensão "Live Server" do VS Code, etc.).
> Só não abra o `index.html` direto com `file://`, pois alguns navegadores
> bloqueiam `fetch` nesse modo.
>
> Se o backend estiver rodando em outra porta/host, ajuste a constante
> `API_BASE` no topo de `frontend/script.js`.

### Rodando os testes automatizados (opcional)

```bash
cd backend
source venv/bin/activate
pytest
```

## Exemplo de uso

1. Com backend (porta 8000) e frontend (porta 5500) rodando, abra
   `http://localhost:5500`. O sistema já vem com 4 contas de demonstração
   (2 corrente, 2 poupança).
2. Selecione a conta **Ana Souza** (corrente, saldo R$ 1.000,00) no seletor.
3. Na aba **Saque**, digite `200` e confirme. A API responde com o novo saldo
   (R$ 1.000 − R$ 200 − R$ 1,00 de tarifa = **R$ 799,00**) e um recibo aparece
   na tela.
4. Troque para a aba **Transferência**, escolha **Bruno Lima** (poupança) como
   destino, informe `50` e confirme. O saldo de Ana cai mais R$ 51,00
   (valor + tarifa) e o de Bruno sobe R$ 50,00 (sem tarifa, conforme a regra
   da poupança).
5. Tente um saque que ultrapasse o limite (ex.: sacar R$ 600 de uma conta
   corrente com saldo R$ 50) — a API recusa com HTTP 400 e a mensagem
   explicando o motivo aparece tanto no formulário quanto no recibo de erro.

## Observações

- **Persistência:** as contas ficam em um repositório em memória
  (`backend/app/store.py`), populado com 4 contas de exemplo ao iniciar o
  servidor. Reiniciar o backend zera os dados — isso foi uma escolha
  deliberada para manter a entrega simples e fácil de rodar em qualquer
  máquina, sem exigir banco de dados.
- **Regras de negócio** (R1 e R2 da especificação) ficam isoladas em
  `backend/app/services.py`, sem nenhuma dependência de HTTP, e são cobertas
  por 11 testes automatizados em `backend/tests/test_business_rules.py`
  (saque/transferência em conta corrente e poupança, limite de cheque
  especial, tarifa, validações de valor e de contas inexistentes/iguais).
- **Diferencial implementado:** transferência entre contas, com a tarifa
  sendo cobrada apenas da conta de origem (a conta corrente que origina a
  operação), conforme a regra R1.
- **Dinheiro como `Decimal`:** todos os cálculos monetários no backend usam
  `decimal.Decimal` (não `float`), evitando erros de arredondamento.
- **Criação de contas:** o frontend tem um link "+ nova conta" (no painel da
  conta) que chama `POST /api/contas`, útil para testar com mais cenários
  além das 4 contas de demonstração.
- **Limitação conhecida:** não há autenticação/autorização — fora do escopo
  do desafio.
