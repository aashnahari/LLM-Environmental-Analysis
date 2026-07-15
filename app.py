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
model_df = pd.DataFrame([totals_row(m, t) for m, t in by_model(records).items()]).set_index("")

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
