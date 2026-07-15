# LLM Environmental Impact

A small Python tool that estimates the energy, water, and carbon footprint of Cedars-Sinai's LLM usage — ChatGPT, Codex, Azure OpenAI, and AWS Bedrock (mostly Claude). Feed it a usage export and it returns kWh, liters of water, and kg of CO2e, broken down by source and model.

## Why

We don't have a real way to answer "how much does our LLM usage cost the environment." Vendor dashboards report dollars, not resource use, and dollars don't map cleanly to compute — a short chat message and a long reasoning call can cost the same but use very different amounts of energy. This tool uses published research instead of guesswork to close that gap.

## How it works

Each source has its own adapter that normalizes whatever data it gives us — tokens, dollars, message counts — into one shared record: model, host, and token counts. From there:

1. Energy is estimated per model using a formula fit to published benchmark data (Jegham et al., 2025), since no vendor publishes their own per-query energy numbers.
2. That energy converts to water and carbon using published infrastructure factors (cooling overhead, water use, grid carbon intensity) that depend on *which cloud actually ran the model*, not which product billed for it. ChatGPT, Codex, and Azure OpenAI all run on Microsoft's infrastructure; only Bedrock runs on AWS's. That distinction matters more than which of the four "sources" a query came from.

## What's solid vs. what's a guess

Azure is the best source — we get real token counts. Codex is close behind. Bedrock usually only gives us dollars, so tokens get backed out from spend using published pricing plus an assumed input:output split. ChatGPT is the weakest link: it bills per message, not per token, so token counts there are an assumption based on message tier — flagged as such wherever it shows up in the output.

The energy numbers themselves are a research estimate, not a settled fact. I checked them against five independent papers plus OpenAI's and Google's own public disclosures. They land in the middle of a fairly wide published range — close to some estimates, meaningfully higher than others (Google's own measured production number in particular runs several times lower). Claude has no vendor disclosure to check against at all, so that number carries more uncertainty than GPT-4o's does.

## Running it

Set up once:
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Command line:
```
.venv/bin/python3 main.py --azure sample_data/azure_sample.json --codex sample_data/codex_sample.json --bedrock sample_data/bedrock_sample.json --chatgpt sample_data/chatgpt_sample.json
```

Dashboard:
```
.venv/bin/streamlit run app.py
```

`sample_data/` has a made-up example file per source if you just want to see it run.

## Layout

- `schema.py` — the shared record shape every adapter produces
- `energy_model.py` — tokens → Wh
- `infra_factors.py` — Wh → water/carbon, by host
- `assumptions.py` — every guessed constant, in one place, documented
- `adapters/` — one file per source, turns raw usage data into the shared record shape
- `aggregate.py` — sums records into totals
- `main.py` — CLI
- `app.py` — Streamlit dashboard

## What's not done yet

- Real export samples from Azure, Bedrock, and ChatGPT — the adapters currently use placeholder field names and will need adjusting once we pull actual data
- Calibrating the ChatGPT and Bedrock assumptions against real usage
- Automated tests
