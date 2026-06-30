"""Schemas Pydantic usados pela API (request/response).

Valores monetários trafegam como `float` no JSON (mais natural para o
frontend), mas são convertidos para `Decimal` assim que entram na
camada de serviço — ver `services.py`.
"""
from pydantic import BaseModel, Field

from app.models import AccountType


class AccountCreate(BaseModel):
    owner_name: str = Field(..., min_length=1, description="Nome do titular da conta")
    type: AccountType
    initial_balance: float = Field(0.0, ge=0, description="Saldo inicial (não pode ser negativo)")


class AccountOut(BaseModel):
    id: str
    owner_name: str
    type: AccountType
    balance: float

    @classmethod
    def from_account(cls, account) -> "AccountOut":
        return cls(
            id=account.id,
            owner_name=account.owner_name,
            type=account.type,
            balance=float(account.balance),
        )


class SaqueRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Valor a sacar (deve ser maior que zero)")


class TransferenciaRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Valor a transferir (deve ser maior que zero)")
    destino_id: str = Field(..., description="ID da conta de destino")


class SaqueResponse(BaseModel):
    conta: AccountOut
    valor_saque: float
    tarifa: float
    mensagem: str


class TransferenciaResponse(BaseModel):
    origem: AccountOut
    destino: AccountOut
    valor_transferencia: float
    tarifa: float
    mensagem: str
