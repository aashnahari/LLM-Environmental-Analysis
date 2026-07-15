# LLM Environmental Impact

A small Python tool that estimates the energy, water, and carbon footprint of Cedars-Sinai's LLM usage — ChatGPT, Codex, Azure OpenAI, and AWS Bedrock (mostly Claude). Feed it a usage export and it returns kWh, liters of water, and kg of CO2e, broken down by source and model.

## Why

We don't have a real way to answer "what is the environmental impact of our LLM usage." Vendor dashboards report dollars, not resource use, and dollars don't map cleanly to compute since a short chat message and a long reasoning call can cost the same but use very different amounts of energy. 

## How it works

Each source has its own adapter that normalizes whatever data it gives us — tokens, dollars, message counts — into one shared record: model, host, and token counts. From there:

1. Energy is estimated per model using a formula fit to published benchmark data (Jegham et al., 2025), since no vendor publishes their own per-query energy numbers.
2. That energy converts to water and carbon using published infrastructure factors (cooling overhead, water use, grid carbon intensity) that depend on which cloud actually ran the model (the host), not which product billed for it. ChatGPT, Codex, and Azure OpenAI all run on Microsoft's infrastructure and only Bedrock runs on AWS's. This matters more than which of the four "sources" a query came from.

## What's known vs. what's estimated

Azure is the best source in terms of vendor-provided data since we get real token counts. Codex is close behind. Bedrock usually only gives us dollars, so tokens are estimated using published pricing plus an assumed input:output split. ChatGPT is the weakest source of data as it bills per message, not per token, so token counts there are an assumption based on message tier (instant, thinking, or pro).

The energy numbers themselves are a research estimate. I checked them against five independent papers plus OpenAI's and Google's own public disclosures. They land in the middle of a fairly wide published range, being close to some estimates while meaningfully higher than others (Google's own measured production number in particular runs several times lower). Claude has no vendor disclosure to check against at all, so that number carries more uncertainty than GPT-4o's does. If anything, these numbers could be interpreted as a maximum level of impact.

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

`sample_data/` has a made-up example file per source to run the calculator before we have access to the logs.

## Layout

- `schema.py` — the shared record shape every adapter produces
- `energy_model.py` — tokens → Wh
- `infra_factors.py` — Wh → water/carbon, by host
- `assumptions.py` — every guessed constant
- `adapters/` — turns raw usage data into the shared record shape
- `aggregate.py` — sums records into totals
- `main.py` — CLI
- `app.py` — Streamlit dashboard

## What's left

- Real export samples from Azure, Bedrock, and ChatGPT (the adapters currently use placeholder field names and will need adjusting once we pull actual data)
- Calibrating the ChatGPT and Bedrock assumptions against real usage
