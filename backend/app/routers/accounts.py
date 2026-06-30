"""Rotas HTTP do Banco.

Endpoints:
- GET    /api/contas               -> lista todas as contas
- GET    /api/contas/{id}          -> detalhe de uma conta
- POST   /api/contas                -> cria uma nova conta
- POST   /api/contas/{id}/saque     -> realiza um saque (regra obrigatória)
- POST   /api/contas/{id}/transferencia -> transfere para outra conta (diferencial)
"""
from fastapi import APIRouter, HTTPException

from app.schemas import (
    AccountCreate,
    AccountOut,
    SaqueRequest,
    SaqueResponse,
    TransferenciaRequest,
    TransferenciaResponse,
)
from app.services import BankService, BusinessError, NotFoundError, to_decimal
from app.store import store

router = APIRouter(prefix="/api/contas", tags=["contas"])
service = BankService(store)


@router.get("", response_model=list[AccountOut])
def listar_contas():
    return [AccountOut.from_account(a) for a in service.list_accounts()]


@router.get("/{conta_id}", response_model=AccountOut)
def obter_conta(conta_id: str):
    try:
        account = service.get_account(conta_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AccountOut.from_account(account)


@router.post("", response_model=AccountOut, status_code=201)
def criar_conta(payload: AccountCreate):
    try:
        account = service.create_account(
            owner_name=payload.owner_name,
            type_=payload.type,
            initial_balance=to_decimal(payload.initial_balance),
        )
    except BusinessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AccountOut.from_account(account)


@router.post("/{conta_id}/saque", response_model=SaqueResponse)
def sacar(conta_id: str, payload: SaqueRequest):
    try:
        account, tarifa = service.sacar(conta_id, to_decimal(payload.amount))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SaqueResponse(
        conta=AccountOut.from_account(account),
        valor_saque=payload.amount,
        tarifa=float(tarifa),
        mensagem=f"Saque de R$ {payload.amount:.2f} realizado com sucesso.",
    )


@router.post("/{conta_id}/transferencia", response_model=TransferenciaResponse)
def transferir(conta_id: str, payload: TransferenciaRequest):
    try:
        origem, destino, tarifa = service.transferir(
            conta_id, payload.destino_id, to_decimal(payload.amount)
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TransferenciaResponse(
        origem=AccountOut.from_account(origem),
        destino=AccountOut.from_account(destino),
        valor_transferencia=payload.amount,
        tarifa=float(tarifa),
        mensagem=(
            f"Transferência de R$ {payload.amount:.2f} de {origem.owner_name} "
            f"para {destino.owner_name} realizada com sucesso."
        ),
    )
