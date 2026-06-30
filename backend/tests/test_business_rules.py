"""Testes das regras de negócio (seção 6 da especificação).

Rodar com: pytest
"""
from decimal import Decimal

import pytest

from app.models import Account, AccountType
from app.services import BankService, BusinessError, NotFoundError
from app.store import AccountStore


@pytest.fixture
def service():
    s = AccountStore()  # store isolado por teste, sem o seed de demonstração
    return BankService(s)


def nova_conta(service, tipo, saldo):
    return service.create_account("Titular Teste", tipo, Decimal(str(saldo)))


# --- Saque: Conta Corrente (R1) --------------------------------------------

def test_saque_corrente_cobra_tarifa_de_1_real(service):
    conta = nova_conta(service, AccountType.CORRENTE, "100.00")
    conta_atualizada, tarifa = service.sacar(conta.id, Decimal("50.00"))
    assert tarifa == Decimal("1.00")
    assert conta_atualizada.balance == Decimal("49.00")  # 100 - 50 - 1


def test_saque_corrente_pode_usar_cheque_especial_ate_500(service):
    conta = nova_conta(service, AccountType.CORRENTE, "0.00")
    conta_atualizada, _ = service.sacar(conta.id, Decimal("499.00"))
    # 0 - 499 - 1 (tarifa) = -500.00, exatamente no limite
    assert conta_atualizada.balance == Decimal("-500.00")


def test_saque_corrente_nao_pode_ultrapassar_limite_de_500(service):
    conta = nova_conta(service, AccountType.CORRENTE, "0.00")
    with pytest.raises(BusinessError):
        # 0 - 499.01 - 1 = -500.01 -> ultrapassa o limite
        service.sacar(conta.id, Decimal("499.01"))


# --- Saque: Conta Poupança (R2) --------------------------------------------

def test_saque_poupanca_nao_cobra_tarifa(service):
    conta = nova_conta(service, AccountType.POUPANCA, "100.00")
    conta_atualizada, tarifa = service.sacar(conta.id, Decimal("100.00"))
    assert tarifa == Decimal("0.00")
    assert conta_atualizada.balance == Decimal("0.00")


def test_saque_poupanca_nao_pode_ficar_negativa(service):
    conta = nova_conta(service, AccountType.POUPANCA, "50.00")
    with pytest.raises(BusinessError):
        service.sacar(conta.id, Decimal("50.01"))


# --- Validações gerais -------------------------------------------------------

def test_saque_valor_zero_ou_negativo_e_rejeitado(service):
    conta = nova_conta(service, AccountType.CORRENTE, "100.00")
    with pytest.raises(BusinessError):
        service.sacar(conta.id, Decimal("0.00"))


def test_saque_em_conta_inexistente_levanta_not_found(service):
    with pytest.raises(NotFoundError):
        service.sacar("id-que-nao-existe", Decimal("10.00"))


# --- Transferência (diferencial) ---------------------------------------------

def test_transferencia_corrente_para_poupanca_cobra_tarifa_so_da_origem(service):
    origem = nova_conta(service, AccountType.CORRENTE, "100.00")
    destino = nova_conta(service, AccountType.POUPANCA, "10.00")

    origem_atualizada, destino_atualizada, tarifa = service.transferir(
        origem.id, destino.id, Decimal("20.00")
    )

    assert tarifa == Decimal("1.00")
    assert origem_atualizada.balance == Decimal("79.00")  # 100 - 20 - 1
    assert destino_atualizada.balance == Decimal("30.00")  # 10 + 20, sem tarifa


def test_transferencia_poupanca_nao_cobra_tarifa_e_nao_pode_negativar(service):
    origem = nova_conta(service, AccountType.POUPANCA, "20.00")
    destino = nova_conta(service, AccountType.CORRENTE, "0.00")

    origem_atualizada, destino_atualizada, tarifa = service.transferir(
        origem.id, destino.id, Decimal("20.00")
    )
    assert tarifa == Decimal("0.00")
    assert origem_atualizada.balance == Decimal("0.00")
    assert destino_atualizada.balance == Decimal("20.00")

    with pytest.raises(BusinessError):
        service.transferir(origem.id, destino.id, Decimal("0.01"))


def test_transferencia_para_a_mesma_conta_e_rejeitada(service):
    conta = nova_conta(service, AccountType.CORRENTE, "100.00")
    with pytest.raises(BusinessError):
        service.transferir(conta.id, conta.id, Decimal("10.00"))


def test_transferencia_respeita_limite_de_cheque_especial(service):
    origem = nova_conta(service, AccountType.CORRENTE, "0.00")
    destino = nova_conta(service, AccountType.POUPANCA, "0.00")
    with pytest.raises(BusinessError):
        # 0 - 499.01 - 1 = -500.01 -> ultrapassa o limite de R$500
        service.transferir(origem.id, destino.id, Decimal("499.01"))
