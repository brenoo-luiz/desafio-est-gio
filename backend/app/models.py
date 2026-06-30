"""Modelos de domínio do Banco.

As contas vivem em memória (ver `store.py`). Usamos `Decimal` para todo
valor monetário, evitando os erros de arredondamento típicos de `float`
em cálculos financeiros.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class AccountType(str, Enum):
    CORRENTE = "corrente"
    POUPANCA = "poupanca"


# Regras de negócio (seção 6 da especificação)
TARIFA_OPERACAO = Decimal("1.00")  # cobrada apenas na conta corrente
LIMITE_CHEQUE_ESPECIAL = Decimal("500.00")  # apenas conta corrente


@dataclass
class Account:
    owner_name: str
    type: AccountType
    balance: Decimal
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def tarifa(self) -> Decimal:
        """Tarifa cobrada por saque/transferência, conforme o tipo de conta (R1/R2)."""
        return TARIFA_OPERACAO if self.type == AccountType.CORRENTE else Decimal("0.00")

    @property
    def limite(self) -> Decimal:
        """Limite de saldo negativo permitido (cheque especial)."""
        return LIMITE_CHEQUE_ESPECIAL if self.type == AccountType.CORRENTE else Decimal("0.00")
