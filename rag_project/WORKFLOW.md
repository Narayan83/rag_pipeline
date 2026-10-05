# How this project works

This assistant answers questions about inspection reports and criteria documents (Acts, Rules, and Government Orders).

Files go in first. They are split into pieces and saved in PostgreSQL. When you ask a question, the chat searches those database rows. It does not open the original files again.

Settings live in `config.yaml`: database, folder paths, model addresses, how many passages to fetch (`top_k`, currently 5), and how much text to send to the model (`max_context_length`, currently 8000 characters).

The chat page is at `http://127.0.0.1:8080`.

---

## 1. Where the files sit

| Folder | What you put there |
| --- | --- |
| `ir_documents` | Inspection reports (PDF, Word, markdown, or text) |
| `criteria_documents` | Acts, Rules, and Government Orders |
| `data/markdown` | Markdown copies of the criteria documents only |

Inspection reports are not saved as markdown files. Criteria documents are.

---

## 2. Putting documents into the database

Press **Ingest documents** on the chat page, or run the ingest step. Each file is read once, then stored in six tables.

### Reading the file

- A PDF is sent to the OCR service, page by page, and turned into text.
- If OCR cannot be reached, the file is read locally instead.
- Word files are read locally. Markdown and text files are read as they are.

### Inspection reports

1. Read the file. Do not write a markdown copy.
2. Pull out details such as state, department, office, district, audit period, IR number, title, year, and auditee.
3. Save one row in `ir_master`.
4. Split the text:
   - Part I and the other non-finding parts become one chunk each.
   - Part II becomes one chunk per audit observation.
   - Tables are lifted out and stored whole, not mixed into the prose.
5. Save prose in `ir_chunks` and tables in `ir_tables`.

### Criteria documents

1. Read the file and write a markdown copy under `data/markdown`.
2. Save one row in `criteria_master`, including the path of that markdown file and whether it is an Act, Rules, or a Government Order.
3. Chunk from the markdown file, not from the original file:
   - Keep the legal shape: Act, Section, Sub-section, Proviso.
   - The full section is the parent. Short sentences inside it are children.
   - Tables are stored whole, separate from the prose.
4. Save prose in `criteria_chunks` and tables in `criteria_tables`.

Running ingest again for the same file name updates that document instead of creating a second copy.

### The six tables

| Table | What it holds |
| --- | --- |
| `ir_master` | One row per inspection report, plus the details used to narrow a search |
| `criteria_master` | One row per Act, Rules, or Government Order |
| `ir_chunks` | Inspection-report passages |
| `criteria_chunks` | Criteria passages. A child row points at its parent section |
| `ir_tables` | Tables taken from inspection reports, kept whole |
| `criteria_tables` | Tables taken from criteria documents, kept whole |

### Embeddings

Each searchable passage can also store a numeric vector from the embedding service (`bge-m3`). That vector is what similarity search uses.

Inspection-report chunks are embedded. For criteria documents, the short child sentences are embedded. A search hit on a child returns the parent section, so the answer has the full context.

Until a row has a vector, search falls back to matching important words in the text.

---

## 3. How Yukta is used

Yes. The retrieval requirement is a Yukta agent system, and that is what runs the chat. The code is in `app/agents.py`. It follows the Quick Start and Tools sections of the Yukta README: `create_agent`, `SystemPrompt`, `AgentConfig`, a remote LLM client, and custom tools on a `ToolProcessor`.

Ingestion only fills the database. It does not ask the model anything, so it does not create a Yukta agent. Every question does.

A new pair of agents is built for each message. Chat history is not saved between questions.

### Yukta pieces this project calls

| Yukta piece | What we use it for |
| --- | --- |
| `create_agent` | Builds the orchestrator and the researcher, the same constructor as the README quick start |
| `SystemPrompt` | Holds each agent's instructions, including the guardrails |
| `AgentConfig` | Sets temperature and how many steps the agent may take. Saved chat history is off |
| `RemoteEndpointClient` | The README's client for any OpenAI-compatible chat endpoint. It calls `llm_url` and `llm_model` from `config.yaml` |
| `Tool` | Defines one action the researcher may call |
| `ToolParameter` | The inputs for that action. Every search tool takes a `query` string |
| `ToolType.CUSTOM` | The README type for a tool whose body is a Python function |
| `ToolProcessor` | Registers the tools and runs the one the model selects |
| `agent.invoke` | Runs the agent. The default call lets the model use tools. A later call can answer from text only |

The README also documents ecosystem YAML, teams, memory, MCP tools, and sandbox. This chat does not use those. It does send one trace per question to Opik. See the logging section below.

### The two agents

**Orchestrator.** `create_agent` with a `SystemPrompt`, `RemoteEndpointClient`, and `AgentConfig` (`max_iter` 2). No tools. Every message goes to this agent first. There is no canned reply list.

- A greeting, a thank-you, or a question about who the assistant is (for example “are you Narayan”) is answered by the model in one or two sentences.
- A question about an inspection report, an audit finding, an Act, a Rule, a Government Order, a section, a proviso, or a table is passed to the researcher as two lines: `ROUTE:researcher` and `QUESTION:`.
- Anything else gets a polite note that it is outside this project.

**Researcher.** The same Yukta constructor, with `max_iter` 6, plus a `ToolProcessor`. Its prompt says to call a Yukta tool before answering, and not to print a sources list. The chat page shows sources separately.

`invoke` is the README's agent call. The model chooses a tool, Yukta runs that function, then the model writes the answer from what the tool returned. If the model never calls a tool, the same database search still runs, and a second `invoke` (tools turned off) writes the answer from those rows.

### Yukta tools on the researcher

These are Yukta `Tool` objects, registered with `processor.add_tool`, which is the README pattern. The function inside each tool is our database query. Yukta validates the arguments, calls the function, and feeds the result back to the model.

| Yukta tool | Function Yukta calls | What it reads |
| --- | --- | --- |
| `search_ir_chunks` | `search_chunks` for inspection reports | `ir_chunks` joined to `ir_master` |
| `search_criteria_chunks` | `search_chunks` for criteria documents | Child rows in `criteria_chunks`, then the parent section |
| `search_ir_tables` | `search_tables` for inspection reports | `ir_tables` |
| `search_criteria_tables` | `search_tables` for criteria documents | `criteria_tables` |
| `calculate_from_tables` | `calculate_table` | Adds up a numeric column when you ask for a total, sum, or average |
| `list_documents` | `list_documents` | `ir_master` and `criteria_master` |

Each search tool returns a short pack of text, limited by `max_context_length`. The rows themselves are kept so the **Sources** button can open them.

### What happens inside a tool call

1. If the question names a state, a department, or an IR number, keep only matching documents.
2. Turn the question into a vector and rank stored vectors. Keep the top `top_k` hits.
3. If there is no vector yet, rank by how many meaningful words from the question appear in the text.
4. Pack the winning passages until `max_context_length` characters.
5. The chat model writes the answer from that text only.

If the model does not call a tool, the same database search still runs, and the model summarises those rows.

The original files are not opened for this step. The passage text is the `chunk` column, or the stored table markdown.

### One message, in order

There is no function that stores fixed replies. “Are you Narayan?” is answered by the orchestrator model, from its instructions.

1. The message enters `ask` in `app/agents.py`. That opens one Opik trace named `MainAgent`.
2. The orchestrator runs. It has no tools.
   - A greeting, thanks, or a question about who the assistant is: the model answers in one or two sentences. The researcher is not called.
   - A document question: the model replies with exactly `ROUTE:researcher` and `QUESTION:`.
   - Anything else: the model says the question is outside this project.
3. Only a `ROUTE:researcher` reply continues. That step is logged as the tool `ask_research`. Inside it, the researcher may call the six tools in the table above.
4. The answer is what the chat shows. If database rows were used, **Sources** can open them.

If the orchestrator model cannot be reached, a small word check decides whether to send the question to the researcher or to say it is outside this project. That check is only the fallback.

### Logging

`config.yaml` has a `tracing` block: `enabled`, `project_name` (`narayan_yukta`), and `opik_url`. Each question is flushed to that Opik project when the chat request finishes.

A research question shows `tool:ask_research` with the question under `tasks` and the answer in `yukta.tool.result_data`. The researcher’s own tool calls are nested under that span. A greeting has the `MainAgent` trace and no research tool.

---

## 4. What you see

The chat fills the page. The answer does not list sources underneath it.

If the reply used database rows, a **Sources** button sits on that answer. Click it to read the stored passages: document name, where they sit in the document, and the text from the database. Click again to hide them.

---

## 5. One question, end to end

Example: “What is the audit period of the Punjab ESI hospital inspection report?”

1. The Yukta orchestrator sends it to the researcher.
2. The researcher calls the Yukta tool `search_ir_chunks`, which reads `ir_chunks` for the Punjab medical inspection report.
3. The top rows include Part I of `IR-83EC056E63CB`, which contains “04/2019 to 06/2024”.
4. The model answers with that period.
5. **Sources** on the bubble opens those database rows.
