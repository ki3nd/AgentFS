# Privacy Policy — AgentFS

AgentFS is a Dify agent strategy plugin. It mounts the Dify Knowledge datasets
you select as a read-only virtual filesystem so the agent can explore them with
shell commands. This document explains what data the plugin touches and where it
goes.

## Data the plugin accesses

- **Dataset content.** For each agent run, AgentFS uses the **Knowledge API base
  URL** and **Knowledge API key** you provide to list documents and retrieve
  document/segment content from the datasets you mount. Access is **read-only** —
  the plugin never writes, modifies, or deletes anything in your datasets.
- **Your query and instructions.** The user query and any instruction you set are
  used to run the agent loop.
- **Credentials.** The Knowledge API key is supplied as a secret parameter and is
  used **only** to authenticate calls to the Knowledge API endpoint you configure.

## Where data goes

- Retrieved dataset content and your query are sent to the **LLM model you
  configured in Dify** (through Dify's model runtime) so the agent can produce an
  answer, and pass through the Dify plugin runtime that hosts this plugin.
- HTTP requests go **only** to the Knowledge API base URL you provide.
- No data is sent to any third party other than (a) your own Knowledge API
  endpoint and (b) the model provider you selected in Dify.

## Storage and retention

- Dataset content is held **only in memory**, inside an ephemeral in-process
  virtual filesystem that exists for the duration of a **single agent
  invocation**, and is discarded when the run ends.
- The plugin does **not** persist dataset content, queries, or credentials to
  disk, and keeps **no** database, cache, or logs of your data.

## Telemetry

AgentFS collects **no** analytics or telemetry. It makes no network calls other
than to the Knowledge API endpoint you configure.

## Third-party components

AgentFS uses the `mirage-ai` library (the virtual filesystem engine) and `httpx`
(HTTP client). Both run locally within the plugin process and do not transmit
your data anywhere on their own.

## Contact

For privacy questions, contact the plugin author: **ki3nd**.
