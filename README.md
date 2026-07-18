# AgentFS

**Author:** [ki3nd](https://github.com/ki3nd)  
**Repository:** [github.com/ki3nd/AgentFS](https://github.com/ki3nd/AgentFS)  
**Type:** agent-strategy

Mount Dify Knowledge datasets as a **read-only virtual filesystem** so your agent
can *explore* them with shell commands — `ls`, `tree`, `cat`, `grep`, `search` —
instead of a single top-k retrieval per turn.

## Why

The usual RAG setup gives an agent one retrieval tool per dataset: query in,
top-k chunks out. The agent is blind to structure — it can't list what exists,
look something up exactly, or scope a search to one folder.

AgentFS turns each dataset into a directory tree the agent can browse:

- **`grep`** for exact/literal lookups (where semantic search is weak).
- **`search`** for semantic retrieval, but scoped to a subtree instead of the
  whole dataset.
- **`ls` / `tree` / `cat`** so the agent decides what to read, instead of being
  forced into one top-k shot.

It is built as a Dify **agent strategy** (function-calling loop) and reuses the
[mirage](https://docs.mirage.strukto.ai/python/resource/dify) virtual-filesystem
engine, scoped to Dify datasets only.

## How it works

On each agent run the strategy:

1. Builds an in-process, **read-only** mirage `Workspace`, mounting every dataset
   you list at the folder name you choose.
2. Exposes a single `execute_command` tool to the model. Filesystem commands run
   **locally in-process** against the mounted datasets; any other tools you attach
   are dispatched normally by Dify.
3. Tears the workspace down when the run ends — nothing is persisted between runs.

## Configuration

Everything is set as **strategy parameters** (there is no provider-level
credential — Dify agent strategies do not receive provider credentials):

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `model` | model-selector (`tool-call&llm`) | ✓ | | Must support tool/function calling. |
| `query` | string | ✓ | | The user question. |
| `instruction` | string | | | Extra system instruction. |
| `tools` | array[tools] | | | Passthrough tools, run alongside the filesystem. |
| `datasets` | string | ✓ | | One `mount: dataset_id` per line (see below). |
| `knowledge_base_url` | string | ✓ | | Knowledge API root, e.g. `https://your-dify-host/v1`. |
| `knowledge_api_key` | secret-input | ✓ | | A Dify **dataset** API key with access to the datasets. |
| `maximum_iterations` | number | | 10 | Tool-call rounds (filesystem exploration needs several). |
| `expose_semantic_search` | boolean | | true | Enables the `search` command. |
| `include_workspace_tree` | boolean | | true | Injects a folder-tree overview into the prompt. |
| `truncate_kb` | number | | 50 | Max KB returned per command output. |

### Mounting datasets

`datasets` maps a folder name to a dataset id, one per line:

```
hr: 3f2a…            # -> agent sees /hr
product-kb: 9b71…    # -> agent sees /product-kb
```

The folder name is the mount root the agent navigates. Lines starting with `#`
are ignored.

### Document paths inside a dataset (optional `slug`)

A Dify dataset is a flat bag of documents. To get **nested folders** inside a
mount, give each document a `slug` metadata value (e.g. `2024/q1/leave-policy`).
Documents **without** a slug still appear — flat, under their document name — so
everything works out of the box; slugs just make the tree nicer.

## Available commands

`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `search`, `awk`, `cut`, `rg`,
`sed`, `sort`, `stat`, `tree`, `uniq`.

- `search "<query>" <path>` — semantic retrieval, scoped to `<path>`.
- `grep` — literal text matching.
- All files are treated as plain text. The filesystem is **read-only**: no write
  commands (`cp`, `mv`, `rm`, `>`, `tee`, `mkdir`, `touch`) are available.

Each command returns JSON: `{stdout, stderr, exit_code, truncated}`.

## Example

- **datasets:** `handbook: <dataset-id>`
- **query:** *"Find our remote-work policy and summarize the approval steps."*

The agent might run `tree /handbook`, then `grep -ri "remote work" /handbook`,
then `cat` the matching document, then answer — all within one run.

## Requirements

- Python 3.12
- `dify_plugin>=0.9.0`, `mirage-ai>=0.0.3`, `httpx>=0.28.1`

## Development

```bash
pip install -r requirements.txt
cp .env.example .env      # set INSTALL_METHOD=remote + your debug URL/key
python -m main            # run in remote-debug mode
pytest tests -q           # run the test suite
```

## License

[MIT](LICENSE) © 2026 ki3nd
