"""Camada de serviço: aqui vivem as regras de negócio do Banco (seção 6
da especificação).

R1 — Conta Corrente: cada saque/transferência cobra tarifa de R$ 1,00
    além do valor. O saldo pode ficar negativo até -R$ 500,00 (cheque
    especial) — valor + tarifa juntos não podem ultrapassar o limite.
R2 — Conta Poupança: saques/transferências não têm tarifa e o saldo
    nunca pode ficar negativo.

Esta camada não conhece nada de HTTP — recebe e devolve objetos de
domínio (`Account`) e `Decimal`. A tradução para HTTP acontece no
router (`routers/accounts.py`).
"""
from decimal import ROUND_HALF_UP, Decimal
from typing import Tuple

from app.models import Account, AccountType
from app.store import AccountStore


def to_decimal(value: float) -> Decimal:
    """Converte um float vindo da API para Decimal com 2 casas, evitando
    erros de ponto flutuante em valores monetários."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class BusinessError(Exception):
    """Violação de uma regra de negócio. Mapeada para HTTP 400 pelo router."""


class NotFoundError(Exception):
    """Entidade não encontrada. Mapeada para HTTP 404 pelo router."""


class BankService:
    def __init__(self, store: AccountStore):
        self.store = store

    # --- consultas -----------------------------------------------------
    def list_accounts(self) -> list[Account]:
        return self.store.list_all()

    def get_account(self, account_id: str) -> Account:
        account = self.store.get(account_id)
        if account is None:
            raise NotFoundError(f"Conta '{account_id}' não encontrada.")
        return account

    def create_account(self, owner_name: str, type_: AccountType, initial_balance: Decimal) -> Account:
        if initial_balance < 0:
            raise BusinessError("O saldo inicial não pode ser negativo.")
        account = Account(owner_name=owner_name, type=type_, balance=initial_balance)
        return self.store.add(account)

    # --- regra compartilhada --------------------------------------------
    def _checar_saldo_apos_debito(self, account: Account, novo_saldo: Decimal) -> None:
        if account.type == AccountType.CORRENTE:
            if novo_saldo < -account.limite:
                raise BusinessError(
                    f"Saldo insuficiente: a operação deixaria a conta corrente com saldo de "
                    f"R$ {novo_saldo:.2f}, ultrapassando o limite de cheque especial de "
                    f"R$ {account.limite:.2f}."
                )
        else:  # poupança (R2)
            if novo_saldo < 0:
                raise BusinessError(
                    "Saldo insuficiente: contas poupança não podem ficar com saldo negativo."
                )

    # --- operações -------------------------------------------------------
    def sacar(self, account_id: str, amount: Decimal) -> Tuple[Account, Decimal]:
        if amount <= 0:
            raise BusinessError("O valor do saque deve ser maior que zero.")

        account = self.get_account(account_id)
        tarifa = account.tarifa
        novo_saldo = account.balance - amount - tarifa

        self._checar_saldo_apos_debito(account, novo_saldo)

        account.balance = novo_saldo
        return account, tarifa

    def transferir(self, origem_id: str, destino_id: str, amount: Decimal) -> Tuple[Account, Account, Decimal]:
        if amount <= 0:
            raise BusinessError("O valor da transferência deve ser maior que zero.")
        if origem_id == destino_id:
            raise BusinessError("A conta de origem e a de destino não podem ser a mesma.")

        origem = self.get_account(origem_id)
        destino = self.get_account(destino_id)

        tarifa = origem.tarifa  # a tarifa é cobrada apenas de quem origina a operação
        novo_saldo_origem = origem.balance - amount - tarifa

        self._checar_saldo_apos_debito(origem, novo_saldo_origem)

        origem.balance = novo_saldo_origem
        destino.balance = destino.balance + amount
        return origem, destino, tarifa
