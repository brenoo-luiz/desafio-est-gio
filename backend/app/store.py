"""Repositório em memória das contas.

Não há banco de dados nesta solução (o enunciado deixa "a forma de
preparar as contas" a critério de quem implementa). O processo guarda
tudo em um dicionário em memória e é populado com algumas contas de
exemplo (`seed`) para facilitar os testes manuais pelo frontend.

Os dados são perdidos ao reiniciar o servidor — isso é intencional e
está documentado no README.
"""
from decimal import Decimal
from typing import Dict, Optional

from app.models import Account, AccountType


class AccountStore:
    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}

    def seed(self) -> None:
        """Popula o store com contas de demonstração."""
        demo_accounts = [
            Account(owner_name="Ana Souza", type=AccountType.CORRENTE, balance=Decimal("1000.00")),
            Account(owner_name="Bruno Lima", type=AccountType.POUPANCA, balance=Decimal("500.00")),
            Account(owner_name="Carla Dias", type=AccountType.CORRENTE, balance=Decimal("50.00")),
            Account(owner_name="Diego Alves", type=AccountType.POUPANCA, balance=Decimal("120.00")),
        ]
        for account in demo_accounts:
            self._accounts[account.id] = account

    def list_all(self) -> list[Account]:
        return list(self._accounts.values())

    def get(self, account_id: str) -> Optional[Account]:
        return self._accounts.get(account_id)

    def add(self, account: Account) -> Account:
        self._accounts[account.id] = account
        return account


# Instância única (singleton) compartilhada pela aplicação.
store = AccountStore()
store.seed()
