const API_BASE = "http://localhost:8000/api/contas";
const HEALTH_URL = "http://localhost:8000/api/health";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// ---------- Estado ----------
let contas = [];
let contaSelecionadaId = null;

// ---------- Elementos ----------
const el = {
  apiStatus: document.getElementById("api-status"),
  accountSelect: document.getElementById("account-select"),
  bcOwner: document.getElementById("bc-owner"),
  bcType: document.getElementById("bc-type"),
  bcBalance: document.getElementById("bc-balance"),
  bcRules: document.getElementById("bc-rules"),

  toggleNewAccount: document.getElementById("toggle-new-account"),
  newAccountForm: document.getElementById("new-account-form"),
  naName: document.getElementById("na-name"),
  naType: document.getElementById("na-type"),
  naBalance: document.getElementById("na-balance"),

  tabSaque: document.getElementById("tab-saque"),
  tabTransferencia: document.getElementById("tab-transferencia"),
  formSaque: document.getElementById("form-saque"),
  formTransferencia: document.getElementById("form-transferencia"),
  saqueAmount: document.getElementById("saque-amount"),
  saqueError: document.getElementById("saque-error"),
  transfDestino: document.getElementById("transf-destino"),
  transfAmount: document.getElementById("transf-amount"),
  transfError: document.getElementById("transf-error"),

  receiptsFeed: document.getElementById("receipts-feed"),
  receiptsEmpty: document.getElementById("receipts-empty"),
  clearReceipts: document.getElementById("clear-receipts"),
};

// ---------- Helpers de API ----------
async function api(method, path, body) {
  const res = await fetch(API_BASE + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((d) => d.msg).join(" ")
      : data.detail || "Erro inesperado na API.";
    throw new Error(detail);
  }
  return data;
}

// ---------- Carregamento inicial ----------
async function init() {
  try {
    const res = await fetch(HEALTH_URL);
    if (!res.ok) throw new Error();
    setApiStatus("ok", "API conectada");
  } catch {
    setApiStatus("erro", "API offline");
  }

  try {
    contas = await api("GET", "");
    if (contas.length > 0) {
      contaSelecionadaId = contas[0].id;
    }
    renderAccountSelect();
    renderBalanceCard();
    renderDestinoSelect();
  } catch (err) {
    setApiStatus("erro", "API offline");
    el.receiptsEmpty.textContent =
      "Não foi possível conectar ao backend. Confira se ele está rodando em " + API_BASE;
  }
}

function setApiStatus(state, text) {
  el.apiStatus.dataset.state = state;
  el.apiStatus.textContent = text;
}

// ---------- Render ----------
function renderAccountSelect() {
  el.accountSelect.innerHTML = contas
    .map(
      (c) =>
        `<option value="${c.id}" ${c.id === contaSelecionadaId ? "selected" : ""}>
          ${escapeHtml(c.owner_name)} · ${tipoLabel(c.type)} · ${currency.format(c.balance)}
        </option>`
    )
    .join("");
}

function renderDestinoSelect() {
  const destinos = contas.filter((c) => c.id !== contaSelecionadaId);
  el.transfDestino.innerHTML = destinos
    .map(
      (c) =>
        `<option value="${c.id}">${escapeHtml(c.owner_name)} · ${tipoLabel(c.type)}</option>`
    )
    .join("");
}

function renderBalanceCard() {
  const conta = contas.find((c) => c.id === contaSelecionadaId);
  if (!conta) {
    el.bcOwner.textContent = "—";
    el.bcType.textContent = "—";
    el.bcBalance.textContent = currency.format(0);
    el.bcRules.textContent = "Nenhuma conta cadastrada.";
    return;
  }

  el.bcOwner.textContent = conta.owner_name;
  el.bcType.textContent = tipoLabel(conta.type);
  el.bcType.dataset.type = conta.type;

  el.bcBalance.textContent = currency.format(conta.balance);
  el.bcBalance.dataset.negative = conta.balance < 0 ? "true" : "false";

  el.bcRules.textContent =
    conta.type === "corrente"
      ? "Tarifa de R$ 1,00 por operação · cheque especial até R$ 500,00"
      : "Sem tarifa · saldo não pode ficar negativo";
}

function tipoLabel(type) {
  return type === "corrente" ? "Conta Corrente" : "Conta Poupança";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- Recibos ----------
function addReceipt({ kind, title, lines, message }) {
  el.receiptsEmpty.classList.add("hidden");

  const node = document.createElement("div");
  node.className = "receipt";
  node.dataset.kind = kind;

  const time = new Date().toLocaleTimeString("pt-BR");

  node.innerHTML = `
    <div class="receipt-header">
      <span class="receipt-kind">${title}</span>
      <span>${time}</span>
    </div>
    ${lines
      .map(
        (l) =>
          `<div class="receipt-line"><span class="label">${l.label}</span><span>${l.value}</span></div>`
      )
      .join("")}
    ${message ? `<div class="receipt-msg">${escapeHtml(message)}</div>` : ""}
  `;

  el.receiptsFeed.prepend(node);
}

// ---------- Tabs ----------
el.tabSaque.addEventListener("click", () => switchTab("saque"));
el.tabTransferencia.addEventListener("click", () => switchTab("transferencia"));

function switchTab(tab) {
  const isSaque = tab === "saque";
  el.tabSaque.classList.toggle("active", isSaque);
  el.tabTransferencia.classList.toggle("active", !isSaque);
  el.tabSaque.setAttribute("aria-selected", String(isSaque));
  el.tabTransferencia.setAttribute("aria-selected", String(!isSaque));
  el.formSaque.classList.toggle("hidden", !isSaque);
  el.formTransferencia.classList.toggle("hidden", isSaque);
}

// ---------- Seleção de conta ----------
el.accountSelect.addEventListener("change", () => {
  contaSelecionadaId = el.accountSelect.value;
  renderBalanceCard();
  renderDestinoSelect();
});

// ---------- Nova conta ----------
el.toggleNewAccount.addEventListener("click", () => {
  el.newAccountForm.classList.toggle("hidden");
});

el.newAccountForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const nova = await api("POST", "", {
      owner_name: el.naName.value.trim(),
      type: el.naType.value,
      initial_balance: parseFloat(el.naBalance.value || "0"),
    });
    contas.push(nova);
    contaSelecionadaId = nova.id;
    renderAccountSelect();
    renderBalanceCard();
    renderDestinoSelect();
    el.newAccountForm.reset();
    el.newAccountForm.classList.add("hidden");
  } catch (err) {
    alert(err.message);
  }
});

// ---------- Saque ----------
el.formSaque.addEventListener("submit", async (e) => {
  e.preventDefault();
  el.saqueError.textContent = "";

  const amount = parseFloat(el.saqueAmount.value);
  const contaAntes = contas.find((c) => c.id === contaSelecionadaId);

  try {
    const result = await api("POST", `/${contaSelecionadaId}/saque`, { amount });

    atualizarContaLocal(result.conta);
    renderBalanceCard();
    renderAccountSelect();
    renderDestinoSelect();

    addReceipt({
      kind: "saque",
      title: "Saque",
      lines: [
        { label: contaAntes.type === "corrente" ? "Conta Corrente" : "Conta Poupança", value: result.conta.owner_name },
        { label: "Valor solicitado", value: currency.format(result.valor_saque) },
        { label: "Tarifa", value: currency.format(result.tarifa) },
        { label: "Saldo final", value: currency.format(result.conta.balance) },
      ],
      message: result.mensagem,
    });

    el.formSaque.reset();
  } catch (err) {
    el.saqueError.textContent = err.message;
    addReceipt({
      kind: "erro",
      title: "Saque recusado",
      lines: [
        { label: "Conta", value: contaAntes ? contaAntes.owner_name : "—" },
        { label: "Valor solicitado", value: currency.format(amount || 0) },
      ],
      message: err.message,
    });
  }
});

// ---------- Transferência ----------
el.formTransferencia.addEventListener("submit", async (e) => {
  e.preventDefault();
  el.transfError.textContent = "";

  const amount = parseFloat(el.transfAmount.value);
  const destinoId = el.transfDestino.value;
  const contaOrigemAntes = contas.find((c) => c.id === contaSelecionadaId);
  const contaDestinoAntes = contas.find((c) => c.id === destinoId);

  if (!destinoId) {
    el.transfError.textContent = "Cadastre ao menos mais uma conta para transferir.";
    return;
  }

  try {
    const result = await api("POST", `/${contaSelecionadaId}/transferencia`, {
      amount,
      destino_id: destinoId,
    });

    atualizarContaLocal(result.origem);
    atualizarContaLocal(result.destino);
    renderBalanceCard();
    renderAccountSelect();
    renderDestinoSelect();

    addReceipt({
      kind: "transferencia",
      title: "Transferência",
      lines: [
        { label: "De", value: result.origem.owner_name },
        { label: "Para", value: result.destino.owner_name },
        { label: "Valor", value: currency.format(result.valor_transferencia) },
        { label: "Tarifa", value: currency.format(result.tarifa) },
        { label: "Saldo final (origem)", value: currency.format(result.origem.balance) },
      ],
      message: result.mensagem,
    });

    el.formTransferencia.reset();
  } catch (err) {
    el.transfError.textContent = err.message;
    addReceipt({
      kind: "erro",
      title: "Transferência recusada",
      lines: [
        { label: "De", value: contaOrigemAntes ? contaOrigemAntes.owner_name : "—" },
        { label: "Para", value: contaDestinoAntes ? contaDestinoAntes.owner_name : "—" },
        { label: "Valor solicitado", value: currency.format(amount || 0) },
      ],
      message: err.message,
    });
  }
});

function atualizarContaLocal(contaAtualizada) {
  const idx = contas.findIndex((c) => c.id === contaAtualizada.id);
  if (idx !== -1) contas[idx] = contaAtualizada;
}

// ---------- Limpar recibos ----------
el.clearReceipts.addEventListener("click", () => {
  el.receiptsFeed.innerHTML = "";
  el.receiptsFeed.appendChild(el.receiptsEmpty);
  el.receiptsEmpty.classList.remove("hidden");
});

init();
