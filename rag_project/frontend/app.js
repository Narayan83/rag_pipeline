const thread = document.querySelector("#thread");
const transcript = document.querySelector("#transcript");
const form = document.querySelector("#composer");
const message = document.querySelector("#message");
const ingest = document.querySelector("#ingest");
const historyEl = document.querySelector("#history");
const documentsBtn = document.querySelector("#documents-btn");
const documentsView = document.querySelector("#documents-view");
const chatView = document.querySelector("#chat-view");
const documentList = document.querySelector("#document-list");
const newChatBtn = document.querySelector("#new-chat");
const refreshBtn = document.querySelector("#refresh");

const STORAGE_KEY = "audit-assistant-chats";

let store = loadStore();
let documentsOpen = false;
let documentsLoaded = false;

function loadStore() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (saved && Array.isArray(saved.chats)) {
      saved.chats = saved.chats.filter((chat) => chat.messages && chat.messages.length);
      if (!saved.chats.some((chat) => chat.id === saved.activeId)) {
        saved.activeId = saved.chats[0] ? saved.chats[0].id : null;
      }
      return saved;
    }
  } catch (error) {
    /* start fresh if the saved chats cannot be read */
  }
  return { activeId: null, chats: [] };
}

function saveStore() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function activeChat() {
  return store.chats.find((chat) => chat.id === store.activeId) || null;
}

function ensureChat() {
  let chat = activeChat();
  if (chat) return chat;
  chat = { id: crypto.randomUUID(), title: "New chat", messages: [] };
  store.chats.unshift(chat);
  store.activeId = chat.id;
  saveStore();
  return chat;
}

function showChat() {
  documentsOpen = false;
  documentsView.hidden = true;
  chatView.hidden = false;
  documentsBtn.classList.remove("active");
  documentsBtn.setAttribute("aria-pressed", "false");
}

function renderHistory() {
  historyEl.replaceChildren();
  if (!store.chats.length) {
    const empty = document.createElement("p");
    empty.className = "history-empty";
    empty.textContent = "No chats yet";
    historyEl.append(empty);
    return;
  }
  for (const chat of store.chats) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";
    if (chat.id === store.activeId && !documentsOpen) button.classList.add("active");
    button.textContent = chat.title || "New chat";
    button.title = chat.title || "New chat";
    button.addEventListener("click", () => openChat(chat.id));
    historyEl.append(button);
  }
}

function openChat(id) {
  store.activeId = id;
  saveStore();
  showChat();
  renderThread();
  renderHistory();
  message.focus();
}

function renderThread() {
  thread.replaceChildren();
  const chat = activeChat();
  if (!chat || !chat.messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const title = document.createElement("h2");
    title.textContent = "Ask about the stored documents";
    const note = document.createElement("p");
    note.textContent = "Inspection reports, Acts, Rules, and Government Orders.";
    empty.append(title, note);
    thread.append(empty);
    return;
  }
  for (const item of chat.messages) {
    thread.append(item.role === "user" ? userTurn(item.text) : assistantTurn(item));
  }
  transcript.scrollTop = transcript.scrollHeight;
}

function userTurn(text) {
  const turn = document.createElement("div");
  turn.className = "turn user";
  const label = document.createElement("div");
  label.className = "you-label";
  label.textContent = "You";
  const bubble = document.createElement("div");
  bubble.className = "user-bubble";
  bubble.textContent = text;
  turn.append(label, bubble);
  return turn;
}

function assistantTurn(item) {
  const turn = document.createElement("article");
  turn.className = "turn assistant";
  const label = document.createElement("div");
  label.className = "evidence";
  const dot = document.createElement("span");
  dot.className = "dot";
  const words = document.createElement("span");
  words.textContent = item.pending ? "Searching the database…" : "Evidence-grounded answer";
  label.append(dot, words);
  turn.append(label);
  if (item.pending) return turn;

  const body = document.createElement("div");
  body.className = "answer";
  body.innerHTML = renderMarkdown(item.text);
  turn.append(body);

  const meta = document.createElement("div");
  meta.className = "answer-meta";
  const elapsed = document.createElement("span");
  elapsed.textContent = item.seconds ? formatSeconds(item.seconds) : "";
  const actions = document.createElement("div");
  actions.className = "meta-actions";
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "copy-btn";
  copy.innerHTML = copyIcon() + "Copy";
  copy.addEventListener("click", async () => {
    const copied = await copyText(item.text);
    if (copied) copy.innerHTML = copyIcon() + "Copied";
    else copy.textContent = "Copy failed";
  });
  actions.append(copy);
  meta.append(elapsed, actions);
  turn.append(meta);

  if (item.sources && item.sources.length) {
    const panel = document.createElement("div");
    panel.className = "sources-panel";
    panel.hidden = true;
    for (const source of item.sources) {
      const block = document.createElement("article");
      block.className = "source-item";
      const title = document.createElement("strong");
      title.textContent = source.document_name || "Stored passage";
      const path = document.createElement("div");
      path.className = "source-path";
      path.textContent = source.hierarchy_path || "";
      const passage = document.createElement("p");
      passage.textContent = source.chunk || "";
      block.append(title, path, passage);
      panel.append(block);
    }
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sources-toggle";
    toggle.textContent = `Sources (${item.sources.length})`;
    toggle.setAttribute("aria-expanded", "false");
    toggle.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
      toggle.setAttribute("aria-expanded", String(!panel.hidden));
    });
    actions.append(toggle);
    turn.append(panel);
  }
  return turn;
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.append(area);
    area.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (copyError) {
      ok = false;
    }
    area.remove();
    return ok;
  }
}

function copyIcon() {
  return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="1.5"/><path d="M6 16H5.5A1.5 1.5 0 0 1 4 14.5v-9A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5V6"/></svg>`;
}

function formatSeconds(seconds) {
  const value = Number(seconds);
  if (!Number.isFinite(value)) return "";
  return value < 10 ? `${value.toFixed(1)} s` : `${Math.round(value)} s`;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inlineMarkdown(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdown(text) {
  const lines = String(text || "").replace(/\r\n/g, "\n").split("\n");
  const parts = [];
  let list = null;
  const closeList = () => {
    if (!list) return;
    parts.push(list.ordered ? `<ol>${list.items.join("")}</ol>` : `<ul>${list.items.join("")}</ul>`);
    list = null;
  };
  for (const line of lines) {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (bullet || numbered) {
      const ordered = Boolean(numbered);
      if (!list || list.ordered !== ordered) {
        closeList();
        list = { ordered, items: [] };
      }
      list.items.push(`<li>${inlineMarkdown((bullet || numbered)[1])}</li>`);
      continue;
    }
    closeList();
    if (!line.trim()) continue;
    parts.push(`<p>${inlineMarkdown(line)}</p>`);
  }
  closeList();
  return parts.join("") || "<p></p>";
}

function resizeMessage() {
  message.style.height = "auto";
  message.style.height = `${Math.min(message.scrollHeight, 128)}px`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = message.value.trim();
  if (!text) return;
  showChat();
  const chat = ensureChat();
  if (chat.messages.length === 0) {
    chat.title = text.length > 48 ? `${text.slice(0, 48).trim()}…` : text;
  }
  chat.messages.push({ role: "user", text });
  saveStore();
  message.value = "";
  resizeMessage();
  renderHistory();
  renderThread();

  const pending = { role: "assistant", text: "", pending: true };
  chat.messages.push(pending);
  renderThread();
  const started = performance.now();
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await response.json();
    const seconds = (performance.now() - started) / 1000;
    chat.messages.pop();
    if (!response.ok) {
      chat.messages.push({
        role: "assistant",
        text: data.detail || "The request failed.",
        sources: [],
        seconds,
      });
    } else {
      chat.messages.push({
        role: "assistant",
        text: data.answer || "",
        sources: data.sources || [],
        seconds,
      });
    }
  } catch (error) {
    chat.messages.pop();
    chat.messages.push({
      role: "assistant",
      text: "The assistant could not be reached.",
      sources: [],
      seconds: (performance.now() - started) / 1000,
    });
  }
  saveStore();
  renderThread();
});

message.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
message.addEventListener("input", resizeMessage);

newChatBtn.addEventListener("click", () => {
  store.chats = store.chats.filter((chat) => chat.messages.length > 0);
  store.activeId = null;
  saveStore();
  showChat();
  renderHistory();
  renderThread();
  message.focus();
});

documentsBtn.addEventListener("click", async () => {
  documentsOpen = true;
  chatView.hidden = true;
  documentsView.hidden = false;
  documentsBtn.classList.add("active");
  documentsBtn.setAttribute("aria-pressed", "true");
  renderHistory();
  if (!documentsLoaded) await loadDocuments();
});

refreshBtn.addEventListener("click", () => {
  location.reload();
});

async function loadDocuments() {
  documentList.replaceChildren();
  const status = document.createElement("p");
  status.className = "doc-status";
  status.textContent = "Loading documents…";
  documentList.append(status);
  try {
    const response = await fetch("/api/documents");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not load documents");
    documentsLoaded = true;
    renderDocuments(data.documents || []);
  } catch (error) {
    documentsLoaded = false;
    documentList.replaceChildren();
    const failed = document.createElement("p");
    failed.className = "doc-status";
    failed.textContent = error.message;
    documentList.append(failed);
  }
}

function renderDocuments(documents) {
  documentList.replaceChildren();
  if (!documents.length) {
    const empty = document.createElement("p");
    empty.className = "doc-empty";
    empty.textContent = "No documents are stored yet. Ingest the folders to add them.";
    documentList.append(empty);
    return;
  }
  const groups = [
    ["Inspection reports", documents.filter((doc) => doc.document_type === "ir_document")],
    ["Criteria", documents.filter((doc) => doc.document_type !== "ir_document")],
  ];
  for (const [label, items] of groups) {
    if (!items.length) continue;
    const group = document.createElement("section");
    group.className = "doc-group";
    const heading = document.createElement("h3");
    heading.textContent = label;
    group.append(heading);
    for (const doc of items) {
      const card = document.createElement("article");
      card.className = "doc-card";
      const title = document.createElement("strong");
      title.textContent = doc.document_title || doc.document_name || "Untitled document";
      const meta = document.createElement("div");
      meta.className = "doc-meta";
      meta.textContent = [doc.instrument_kind, doc.state, doc.year, doc.document_name]
        .filter(Boolean)
        .join(" · ");
      card.append(title, meta);
      group.append(card);
    }
    documentList.append(group);
  }
}

ingest.addEventListener("click", async () => {
  ingest.disabled = true;
  ingest.textContent = "Ingesting…";
  try {
    const response = await fetch("/api/ingest", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Ingest failed");
    documentsLoaded = false;
    await loadDocuments();
  } catch (error) {
    const failed = document.createElement("p");
    failed.className = "doc-status";
    failed.textContent = error.message;
    documentList.prepend(failed);
  } finally {
    ingest.disabled = false;
    ingest.textContent = "Ingest documents";
  }
});

renderHistory();
renderThread();
