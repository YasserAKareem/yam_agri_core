# YAM Server - How It Works

---

Let me start with the problem the usual local-AI demos do not solve.

A lot of people can get one model running on one machine. That part is not magic anymore. You install a container, pull a model, open a browser, and for a few hours it feels like the future has arrived in your office.

Then real life begins.

Somebody wants user accounts. Somebody wants a second model. Somebody wants documents, not just chat. Somebody wants logs when something fails. Somebody wants to know who spent the tokens, which model answered, where the prompt went, and whether the thing can survive a reboot without turning into a science project.

That is the gap between "I have a chat window" and "I have a platform."

YAM Server is meant to live in that gap.

It is not a single container. It is not just a clever prompt wrapped around a model. And it is not a fork of Dream Server with a new coat of paint. It is a new, Compose-first AI platform for a small team - the kind of system you can run on a serious workstation, explain to a non-expert, and still trust enough that an engineer would not be embarrassed to build on top of it.

The core idea is simple: keep the user experience approachable, keep the platform boundaries clean, and keep the control in your hands.

At the center of YAM Server is a small but opinionated stack:

- **Open WebUI** for the main user interface
- **LiteLLM** for auth, keys, budgets, model catalog, logging, and gateway control
- **vLLM Semantic Router** for routing decisions
- **vLLM** for fast local inference
- **PostgreSQL + pgvector** for application state, documents, and retrieval memory

Around that core, you add the things that make a system dependable rather than merely impressive: Redis, document extraction, embeddings, backups, observability, and eventually automation, research, voice, and media workers.

That is YAM Server.

---

## What We Are Actually Building

When people talk about AI infrastructure, they often talk as if the model is the whole thing.

It is not.

A model is the part that writes the answer. But a usable platform needs a front door, an identity system, routing rules, logs, document memory, health checks, database backups, and some way to keep today's quick experiment from turning into tomorrow's operational mess.

So YAM Server is designed as a **platform**, not a chatbot.

It is **Compose-first**, because the target is a small team, not a giant cluster on day one. It is designed for the kind of machine many people can actually own, including an RTX 4060 with 8 GB of VRAM. It assumes you want text, retrieval, and reliable application behavior first. Voice comes next. Heavy image and video workloads come later, on separate workers when the platform earns them.

That choice matters.

A lot of self-hosted AI projects pretend every box can do every job. YAM Server does not. It starts with a realistic promise:

- One command — detects your GPU, picks the right model, generates credentials, launches everything
- one good user-facing chat system
- one clean gateway
- one local inference engine
- one durable database layer
- one place to grow from

That is enough to build on.

---

## The Team in the Building

I find it helps to picture YAM Server as a building with a small team inside it. Everyone has a role. Nobody tries to do everybody else's job. And the entire system works because the hallways between them are clear.

The first thing you meet is **Traefik**.

Traefik is the front gate. It answers the outside world, handles stable URLs, terminates TLS, applies basic routing rules, and gives the rest of the building a calm, predictable edge. You do not want every app exposing itself in its own way. You want one front gate.

Inside the lobby sits **Open WebUI**.

Open WebUI is the front desk. It is where users arrive. It remembers conversations. It lets people upload files. It turns a pile of infrastructure into something that feels like a product. If YAM Server is successful, most users will spend their time here and barely think about the rest of the building.

But Open WebUI is not the switchboard. That job belongs to **LiteLLM**.

LiteLLM is one of the most important choices in the whole design. It is the gateway, the key issuer, the budget keeper, the model catalog, and the place where usage becomes visible. Even when everything is local, LiteLLM still matters, because routing through it means you get identity, logging, policy, and model management in one place instead of losing them the moment you stop using a cloud API.

Down the hall is **vLLM Semantic Router**.

This is the traffic cop. Its job is not to be the model. Its job is to decide which local model path should handle a request. In the early life of the system, that may look modest. On a single 8 GB GPU, you may only keep one truly "hot" text model running at a time, with routing logic that is more about future readiness and request shaping than dramatic multi-model orchestration. That is okay. The router still establishes the contract that allows the platform to grow without rewiring everything later.

Then you reach **vLLM** itself.

This is the engine room. vLLM is where local text inference happens. It loads the model, serves the OpenAI-compatible API, streams tokens back, and does the hard work fast enough that the whole experience feels responsive. It is not there to handle budgets, teams, docs, or policy. It is there to turn prompts into answers quickly and reliably.

Now let us talk about memory.

**PostgreSQL + pgvector** is the system memory and document store. PostgreSQL holds what grown-up software always needs to hold: application state, operational metadata, durable records, and things that should still exist tomorrow morning. pgvector extends that memory into semantic retrieval. It lets the platform keep document chunks, embeddings, and similarity search close to the transactional data instead of scattering them into a separate system too early.

Moving around that memory layer is **Redis**.

Redis is the courier. It handles caching, short-lived coordination, and the kind of fast state you do not want to jam into the main database. It becomes more important as soon as concurrency rises, background jobs appear, or the platform starts to feel alive rather than merely functional.

When a user uploads a document, the first person who really reads it is **Tika**.

Tika is the document extractor. PDFs, Word files, messy office documents - it pulls the actual text out so the rest of the platform can work with it. This sounds boring until the first time a beautiful user flow fails because the system never actually extracted usable text. Tika handles that layer of reality.

Then the text goes to the **embeddings service**.

That service is the translator. It turns human language into vectors that pgvector can search meaningfully. Most users never meet it. It just does its work in the background, quietly turning raw text into searchable memory.

And watching the whole place is the **observability stack**.

Call it the watchtower. Whether it is Grafana LGTM or an equivalent stack, this is how you know what happened, why it happened, who triggered it, how slow it was, and what is quietly breaking before the users notice. A local AI platform without observability is not a platform. It is a guess.

That is the core team.

Not enormous. Not theatrical. Just disciplined.

---

## What Happens When You Ask a Question

Let me walk you through the basic chat path, because this is where the architecture stops being abstract.

You open your browser. You type a question into Open WebUI. Maybe it is a coding question. Maybe it is a planning question. Maybe it is just "explain this to me like I am busy and tired."

Open WebUI receives the message, adds the conversation context, applies whatever user-facing tools or document context are in play, and sends the request onward.

But it does **not** talk straight to vLLM.

It goes to LiteLLM first.

That is deliberate.

If Open WebUI talked straight to the model engine, the platform would lose the very things that make it manageable as it grows: keys, teams, limits, model aliasing, logs, usage, and policy. LiteLLM stays in front because local routing does not eliminate governance. It makes governance more important.

So the path looks like this:

```text
Browser
  -> Open WebUI
  -> LiteLLM
  -> vLLM Semantic Router
  -> vLLM
  -> response streams back the same way
```

LiteLLM receives the request with an authenticated key and known context. It applies the model alias or route policy. It hands the request to semantic-router, which decides which local route should handle it. That route points to vLLM. vLLM generates the answer token by token, and the whole response travels back up the same chain until the text appears in the browser.

To the user, it feels like one answer.

To the platform, it is a disciplined chain of responsibility.

---

## What Happens When You Upload a Document

Document workflows are where a lot of self-hosted systems stop being neat.

A chat stack that only answers free-form questions can get away with a surprising amount of sloppiness. The moment you introduce real documents, the platform has to do more than sound clever. It has to extract, transform, index, store, retrieve, and cite.

So in YAM Server, the document path is its own pipeline:

```text
file upload
  -> Open WebUI
  -> Tika
  -> embeddings service
  -> PostgreSQL + pgvector
  -> retrieval on query
  -> LiteLLM
  -> vLLM
```

The user uploads a file in Open WebUI. Open WebUI hands the raw file to Tika, which extracts text from it. That extracted text is chunked and sent to the embeddings service. The embeddings service turns each chunk into vectors. Those chunks and vectors are written into PostgreSQL with pgvector enabled.

Later, when the user asks a question about the document, retrieval happens against that stored memory. The relevant chunks are selected, passed back into the prompt context, and only then sent through LiteLLM and on to the model engine.

That is how the system stops being "a smart autocomplete" and becomes "an assistant that knows my material."

And because that memory lives in PostgreSQL + pgvector rather than a throwaway side database, it can be backed up, restored, inspected, migrated, and managed like the rest of the platform.

---

## What Happens When the System Scales

Here is the part people usually get backward.

When a self-hosted AI system starts to grow, the first instinct is to add more models.

But more models are usually not the first missing piece.

The first missing pieces are the boring, foundational ones:

- caching
- retries
- logs
- traces
- backups
- restore drills
- stable auth
- well-defined routes

That is why **Redis**, **observability**, **gateway auth**, and **database backups** matter before a dramatic model menu does.

Redis absorbs the small, fast coordination tasks that would otherwise make the whole platform feel sticky under load.

Observability tells you whether the slowness is in Open WebUI, LiteLLM, semantic-router, vLLM, embeddings, or the database. Without it, every failure looks like "the AI is slow," which is not a diagnosis.

Gateway auth means users, teams, and future applications can share one control plane instead of inventing credentials per service.

Backups matter because once people trust a system with documents, prompts, team configuration, or workflow state, losing that state is no longer an inconvenience. It is a failure of stewardship.

And that is why YAM Server is careful about the sequence of maturity.

You do not earn the right to call something a platform because it can answer a question. You earn it because it can keep answering questions after restarts, upgrades, mistakes, and growth.

---

## Why This Platform Is Split Into Multiple Repos

Now we get to the part that tends to make small teams nervous: the repo strategy.

The temptation, especially early on, is to put everything into one repository forever. One repo feels simple. One repo feels fast. One repo feels like less overhead.

And for a week or two, it is.

Then the platform grows. Models change faster than docs. Observability changes faster than workflows. Media services change faster than text services. Agents evolve on a different cadence than the gateway. You want one team to change dashboards without risking the routing layer. You want another team to experiment with media workers without having to understand every corner of the core platform.

That is why YAM Server should be a **family of repos**, not a giant drawer full of unrelated things.

Specialized repos create clean ownership boundaries. They make upgrades easier to reason about. They let different parts of the system move at different speeds. They reduce the blast radius of change.

That does not mean the platform becomes fragmented. It means the boundaries are intentional.

The trick is not to create a hundred tiny repos. The trick is to create a set of repos that each own a meaningful surface area.

---

## The Recommended New Repos

Here is the repo map I would recommend for YAM Server from the beginning.

### `yam-server-core`

This is the source of truth for the platform itself.

It holds the Compose files, environment contracts, service configs, bootstrap logic, health checks, secrets conventions, backup jobs, and the wiring for Traefik, Open WebUI, LiteLLM, vLLM Semantic Router, vLLM, PostgreSQL, Redis, Tika, embeddings, and any other service that is part of the core platform contract.

If a service must exist for the platform to boot and make sense, it belongs here.

**Ownership boundary:** platform engineering and DevOps.

### `yam-server-models`

This repo owns the part people often mix into everything else and later regret.

It holds model profiles, alias definitions, semantic-router policies, LiteLLM model mappings, system-prompt defaults, benchmark notes, hardware profiles, quantization guidance, and the decisions about what "fast," "default," or "coder" actually mean in the system.

It does **not** own deployment logic.

**Ownership boundary:** inference and ML runtime engineering.

### `yam-server-observability`

This repo owns the watchtower.

Grafana dashboards, Prometheus rules, Loki and Tempo wiring, alert thresholds, SLO definitions, retention policies, tracing setup, and the operational dashboards that tell you whether the platform is behaving like a product or wobbling like a prototype.

Keeping observability separate means you can evolve monitoring without turning every metrics tweak into a core-platform release.

**Ownership boundary:** SRE and platform reliability.

### `yam-server-agents`

This is where A2A agents, tool wrappers, starter agent definitions, agent prompts, policy packs, and semantic-router route policies tied to agent classes should live.

If the platform grows from "chat with a model" into "delegate work to an agent," this repo becomes the home for that logic. It can move quickly without destabilizing the core gateway and storage layers.

**Ownership boundary:** agent platform team.

### `yam-server-workflows`

This repo owns automation.

n8n flows, event-driven jobs, ingest pipelines, connector logic, scheduled tasks, approval flows, and all the low-code or no-code orchestration that sits above the model and below the business use case. It is where practical automation should be versioned rather than trapped in a browser UI forever.

**Ownership boundary:** automation and integration engineering.

### `yam-server-media`

Media expands faster than text. It deserves room of its own.

This repo should hold optional STT, TTS, image-generation, and later video-worker infrastructure. That includes service definitions, routing contracts, model choices, and any media-specific operational notes.

Keeping it separate protects the text-first platform from getting buried under GPU-hungry creative workflows too early.

**Ownership boundary:** media and multimodal runtime team.

### `yam-server-docs`

This repo holds the explanations, runbooks, ADRs, onboarding guides, architecture notes, diagrams, hardware advice, threat models, and operational playbooks that make the rest of the platform legible.

Good docs are not a side effect. They are part of the system.

**Ownership boundary:** shared, but curated like product infrastructure.

### `yam-server-apps`

This is where optional add-on services belong: research tools, admin helpers, internal line-of-business apps, customer-specific portals, and anything useful that is not part of the platform contract itself.

It keeps experimentation alive without bloating the core.

**Ownership boundary:** application teams and solution builders.

---

## Additional Apps Worth Adding Later

The best add-ons are not the loudest ones. They are the ones that solve the next real bottleneck.

### Add Soon After Core

**Authentik** should arrive early if more than a handful of people are using the system. It gives you OIDC, SSO, and a proper identity story instead of scattered credentials.

**Grafana LGTM** or an equivalent observability bundle should be treated as an early companion, not a luxury. Logs and traces save more time than extra models do.

**n8n** is worth adding as soon as people stop asking only questions and start wanting outcomes. Summaries, approvals, file routing, notifications, and automations all belong here.

**SearXNG** belongs in the "soon after core" category because research and current-information workflows become useful quickly, and a local metasearch layer keeps those workflows grounded without surrendering them to a third-party product.

### Add When Document Workflows Grow

**Langfuse** becomes valuable when prompts, traces, and LLM behavior need to be observed as a product rather than guessed at as a hobby.

**Qdrant** should only be added when pgvector stops being enough. That matters. A lot of teams add a dedicated vector database because it feels modern, not because they need it. YAM Server should resist that temptation until retrieval scale, search features, or operational separation actually justify the extra system.

### Add When Voice Matters

A local **STT** service belongs here when users want to speak naturally instead of type.

A local **TTS** service belongs here when the system needs to respond out loud in a voice that feels usable.

Voice is not the first thing the platform must do well. But once the core is dependable, voice can make the system feel dramatically more human.

### Add When Creative Workflows Matter

An **image worker** belongs here when prompt-to-image becomes a real use case instead of a nice demo.

A **video worker** belongs here later, and on a different operational footing. A base 8 GB GPU box should not pretend it is a video-generation powerhouse. That is a separate worker class, a separate cost profile, and often a separate machine.

---

## Hardware, Scope, and Honesty

Let me be direct about the hardware, because good architecture begins with honesty.

An **RTX 4060 with 8 GB of VRAM** is enough to make YAM Server useful. It is not enough to make it limitless.

It is a solid text-and-retrieval machine. It can support a well-chosen local model, document pipelines, Open WebUI, LiteLLM, pgvector-backed retrieval, and careful growth. It can probably handle light voice work if you are disciplined. It is not the box on which you promise heavyweight local video generation, multiple large hot models, and every creative workflow at once.

That is not a weakness in the design. That is design maturity.

So the honest scope for an 8 GB machine is:

- text first
- embeddings second
- documents early
- voice after the core is calm
- media on separate workers when the platform earns it

The point of the platform is not to pretend every machine is a datacenter. The point is to give one serious machine a serious job and a clean path to grow.

---

## Where This Design Comes From

YAM Server is not being imagined in a vacuum. It borrows the best lesson from Dream Server - explain complex infrastructure like a human being is going to read it - while pushing the platform shape in a more explicitly modular direction.

The design also leans on a few practical truths from the current ecosystem:

- LiteLLM is strongest when it remains the gateway, not an optional side path.
- Open WebUI becomes more valuable when it is treated as the product surface, not the place where infrastructure policy lives.
- vLLM is excellent at inference, but inference alone is not a platform.
- semantic-router is most useful when it establishes a routing contract early, even before the system grows into many backends.
- PostgreSQL + pgvector is often the right first retrieval memory layer because it is operationally legible.

If someone wanted to go read the foundations for this architecture, these are the places I would point them:

- Dream Server reference narrative:
  [HOW-DREAM-SERVER-WORKS.md](https://github.com/Light-Heart-Labs/DreamServer/blob/main/dream-server/docs/HOW-DREAM-SERVER-WORKS.md)
- vLLM Semantic Router:
  [installation guide](https://vllm-semantic-router.com/docs/next/installation/) and [project repo](https://github.com/vllm-project/semantic-router)
- LiteLLM:
  [main docs](https://docs.litellm.ai/) and [Open WebUI integration guide](https://docs.litellm.ai/docs/tutorials/openweb_ui)
- Open WebUI:
  [advanced scaling guidance](https://docs.openwebui.com/getting-started/advanced-topics/scaling/) and [starting with vLLM](https://docs.openwebui.com/getting-started/quick-start/starting-with-vllm/)

---

## The Philosophy

What I want YAM Server to stand for is not simply "run AI locally."

A lot of things can run AI locally.

What matters is whether the result is understandable, maintainable, ownable, and calm under pressure.

That is the deeper promise here.

Not just that your prompts stay close to home. Not just that your costs stay predictable. Not just that your models are under your control.

But that the entire platform is built in a way that respects how systems actually live in the world:

- they grow unevenly
- they break at the edges
- they need clear owners
- they need documentation
- they need backups
- they need room to evolve without becoming a tangle

YAM Server should be the kind of system that starts small, tells the truth about its limits, and gets stronger by becoming more modular rather than more chaotic.

Your gateway. Your models. Your documents. Your routes. Your repos. Your rules.
