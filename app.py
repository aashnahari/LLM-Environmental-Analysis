import json

import pandas as pd
import streamlit as st

from aggregate import Totals, by_model, by_source, total
from main import SOURCE_LOADERS

st.set_page_config(page_title="LLM Environmental Impact")

st.markdown(
    """
    <style>
    div[data-testid="stDecoration"] { display: none; }
    .block-container { padding-top: 3rem; max-width: 760px; }
    [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    </style>
    """,
    unsafe_allow_html=True,
)

SOURCES = [
    {
        "title": "How Hungry is AI? Benchmarking Energy, Water, and Carbon Footprint of LLM Inference",
        "url": "http://arxiv.org/abs/2505.09598",
        "authors": "Jegham, Abdelatti, Koh, Elmoubarki & Hendawi, 2025",
        "note": "Primary source for this app's per-model energy coefficients and Azure/AWS infrastructure factors.",
    },
    {
        "title": "Measuring the Environmental Impact of Delivering AI at Google Scale",
        "url": "http://arxiv.org/abs/2508.15734",
        "authors": "Elsworth et al., 2025",
        "note": "Google's own production measurement of Gemini inference energy, water, and carbon.",
    },
    {
        "title": "The Environmental Impacts of Large Language Models",
        "url": None,
        "authors": "Govil, Mishika",
        "note": "Survey of the architectural and algorithmic factors driving LLM energy use.",
    },
    {
        "title": "Unveiling Environmental Impacts of Large Language Model Serving: A Functional Unit View",
        "url": None,
        "authors": "Wu, Hua & Ding",
        "note": "Proposes a standardized 'functional unit' for comparing carbon emissions across model configurations.",
    },
    {
        "title": "Fair, Practical, and Efficient Carbon Accounting for LLM Serving",
        "url": "https://dl.acm.org/doi/epdf/10.1145/3764944.3764967",
        "authors": None,
        "note": "Carbon-accounting framework for LLM serving emission factors.",
    },
    {
        "title": "The Energy Footprint of LLM-Based Environmental Analysis: LLMs and Domain Products",
        "url": "http://arxiv.org/abs/2604.00053",
        "authors": "Bao, He, Hsu, Manya et al., 2026",
        "note": "Compares energy use of RAG-based climate chatbots against a generic GPT-4o-mini call.",
    },
    {
        "title": "We Did the Math on AI's Energy Footprint. Here's the Story You Haven't Heard.",
        "url": "https://www.technologyreview.com/2025/05/20/1116327/ai-energy-usage-climate-footprint-big-tech/",
        "authors": "MIT Technology Review, 2025",
        "note": "Journalistic investigation into data-center-scale AI energy and carbon.",
    },
    {
        "title": "Sustainable LLM Serving: Environmental Implications, Challenges, and Opportunities",
        "url": "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10765824",
        "authors": None,
        "note": "Survey of environmental challenges specific to LLM serving infrastructure.",
    },
    {
        "title": "Preventing the Immense Increase in the Life-Cycle Energy and Carbon Footprints of LLM-Powered Intelligent Chatbots",
        "url": "https://linkinghub.elsevier.com/retrieve/pii/S2095809924002315",
        "authors": "Jiang, Sonne, Li, You & You, 2024",
        "note": "Life-cycle analysis across eight phases of chatbot development and deployment.",
    },
    {
        "title": "Exploring the Sustainable Scaling of AI Dilemma: A Projective Study of Corporations' AI Environmental Impacts",
        "url": None,
        "authors": "Desroches, Chauvin, Ladan, Vateau, Gosset & Cordier",
        "note": "Projects corporate AI environmental impact, including hardware fabrication and end-of-life.",
    },
    {
        "title": "LLMCarbon: Modeling the End-to-End Carbon Footprint of Large Language Models",
        "url": None,
        "authors": "Faiz, Kaneda, Wang, Osi, Sharma, Chen & Jiang, 2024",
        "note": "Carbon-footprint projection tool covering training, inference, and embodied hardware emissions.",
    },
    {
        "title": "Large Language Models for Energy and Carbon Footprint Optimization: A Comprehensive Survey",
        "url": None,
        "authors": "Yang, Youla",
        "note": "Survey of energy-efficient and carbon-aware LLM design techniques.",
    },
    {
        "title": "From Prompts to Power: Measuring the Energy Footprint of LLM Inference",
        "url": "http://arxiv.org/abs/2511.05597",
        "authors": "Caravaca, Cuevas & Cuevas, 2025",
        "note": "Large-scale measurement study (32,500+ measurements) across GPU configurations and model architectures.",
    },
    {
        "title": "A Deployment-Aware Framework for Carbon- and Water-Efficient LLM Serving",
        "url": "https://www.mdpi.com/2071-1050/17/23/10473",
        "authors": None,
        "note": "Carbon- and water-aware routing framework for LLM serving deployments.",
    },
    {
        "title": "TokenOps: A Compiler-Style Architecture for Token Optimization in LLM API Workflows",
        "url": None,
        "authors": "Lodha, Nitin",
        "note": "Token-reduction techniques aimed at cutting LLM API cost, latency, and carbon footprint.",
    },
    {
        "title": "Emission Factor Recommendation for Life Cycle Assessments with Generative AI",
        "url": "https://pubs.acs.org/doi/10.1021/acs.est.4c12667",
        "authors": "Balaji et al., 2025",
        "note": "AI-assisted method for selecting emission factors in life-cycle assessments.",
    },
    {
        "title": "Energy Costs of Communicating with AI",
        "url": "https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2025.1572947/full",
        "authors": None,
        "note": "Measurement framework for the token-level energy cost of AI communication.",
    },
    {
        "title": "A Comparative Study of AI and Human Programming on Environmental Sustainability",
        "url": "https://www.nature.com/articles/s41598-025-24658-5",
        "authors": None,
        "note": "Benchmarks the energy and carbon footprint of AI-generated versus human-written code.",
    },
    {
        "title": "When Faster Isn't Greener: The Hidden Costs of LLM-Based Code Optimization",
        "url": "https://zenodo.org/doi/10.5281/zenodo.15526179",
        "authors": "Coignion, Quinton & Rouvoy",
        "note": "Finds LLM-based code optimization isn't always energetically justified despite runtime gains.",
    },
    {
        "title": "Reconciling the Contrasting Narratives on the Environmental Impact of Large Language Models",
        "url": "https://www.nature.com/articles/s41598-024-76682-6",
        "authors": None,
        "note": "Survey reconciling conflicting public estimates of LLM environmental impact.",
    },
    {
        "title": "When Every Question Counts: Measuring the Environmental Impact of LLMs in Use",
        "url": "https://medium.com/axionable-ai-and-blockchain/when-every-question-counts-measuring-the-environmental-impact-of-llms-in-use-7e3532092231",
        "authors": "Paul-Étienne Mallet, Axionable",
        "note": "Practitioner write-up on measuring per-query LLM environmental impact.",
    },
    {
        "title": "Sam Altman: Energy for ChatGPT Query Can Power a Lightbulb for Minutes",
        "url": "https://www.businessinsider.com/how-much-energy-does-chatgpt-use-average-query-watts-altman-2025-6",
        "authors": "Business Insider, 2025",
        "note": "Reports OpenAI's own informal per-query energy estimate.",
    },
    {
        "title": "Our Contribution to a Global Environmental Standard for AI",
        "url": "https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai/",
        "authors": None,
        "note": "Vendor statement on AI environmental-impact standardization.",
    },
]

EXAMPLE_ROWS = {
    "azure": {
        "raw_model": "gpt-4o-deployment",
        "input_tokens": 500000,
        "output_tokens": 200000,
        "cached_tokens": 100000,
        "n_requests": 5000,
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
    },
    "codex": {
        "raw_model": "gpt-5.6-sol",
        "input_tokens": 300000,
        "output_tokens": 120000,
        "cached_tokens": 40000,
        "n_requests": 800,
    },
    "bedrock": {
        "raw_model": "anthropic.claude-3-7-sonnet-20250219-v1:0",
        "total_usd": 42.50,
        "n_requests": 300,
    },
    "chatgpt": {"tier": "instant", "n_messages": 2000},
}


def totals_row(label: str, t: Totals) -> dict:
    return {
        "": label,
        "energy (Wh)": round(t.energy_wh, 1),
        "water (L)": round(t.water_l, 2),
        "carbon (kg CO2e)": round(t.carbon_kg, 3),
        "requests": int(t.n_requests),
        "estimated": f"{t.n_estimated}/{t.n_records}",
    }


st.markdown("## LLM environmental impact")

st.sidebar.markdown("**Upload usage exports**")
st.sidebar.caption("JSON list of rows, one dict per row.")
with st.sidebar.expander("Expected format"):
    for source, example in EXAMPLE_ROWS.items():
        st.caption(source)
        st.code(json.dumps(example), language="json")

uploads = {
    source: st.sidebar.file_uploader(source, type="json", key=source)
    for source in ["azure", "codex", "bedrock", "chatgpt"]
}

records = []
errors = []
for source, uploaded in uploads.items():
    if uploaded is None:
        continue
    try:
        rows = json.loads(uploaded.read())
        records.extend(SOURCE_LOADERS[source](rows))
    except Exception as e:
        errors.append(f"{source}: {e}")

for err in errors:
    st.error(err)

with st.expander(f"Sources ({len(SOURCES)})"):
    for src in SOURCES:
        heading = f"**[{src['title']}]({src['url']})**" if src["url"] else f"**{src['title']}**"
        st.markdown(heading)
        byline = " · ".join(part for part in (src["authors"], src["note"]) if part)
        st.caption(byline)

if not records:
    st.caption("Upload at least one usage export in the sidebar to see results.")
    st.stop()

grand_total = total(records)

st.write(
    f"**{grand_total.energy_wh / 1000:,.2f} kWh** &nbsp;·&nbsp; "
    f"**{grand_total.water_l:,.1f} L** water &nbsp;·&nbsp; "
    f"**{grand_total.carbon_kg:,.2f} kg** CO2e &nbsp;·&nbsp; "
    f"{grand_total.n_requests:,.0f} requests",
    unsafe_allow_html=True,
)
st.caption(f"{grand_total.n_estimated} of {grand_total.n_records} records rest on an estimate, not measured tokens.")

source_df = pd.DataFrame([totals_row(s.value, t) for s, t in by_source(records).items()]).set_index("")
source_df.index.name = "source"
model_df = pd.DataFrame([totals_row(m, t) for m, t in by_model(records).items()]).set_index("")
model_df.index.name = "model"

st.write("")
st.markdown("**Energy by source**")
st.bar_chart(source_df["energy (Wh)"], color="#2a78d6", horizontal=True)

st.markdown("**By source**")
st.dataframe(source_df, use_container_width=True)

st.markdown("**By model**")
st.dataframe(model_df, use_container_width=True)

csv = source_df.reset_index().to_csv(index=False).encode("utf-8")
st.download_button("Download by-source CSV", csv, "footprint_by_source.csv", "text/csv")

st.caption(
    "Modeled estimate, not a bill. Coefficients are fit from third-party "
    "benchmark data, not vendor-measured; 'estimated' rows rest on "
    "placeholder assumptions documented in assumptions.py."
)
