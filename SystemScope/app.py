from pathlib import Path
from collections import deque
from time import monotonic

import pandas as pd
import streamlit as st

from monitor import LOW_PERCENT, capacity, computer_details, read_live

st.set_page_config(page_title="SystemScope", layout="wide")
st.title("SystemScope")


def show_details(fields):
    table = pd.DataFrame(list(fields.items()), columns=["Item", "Reading"])
    with st.expander("Computer details and report"):
        st.table(table.astype(str))

    lines = [f"- **{label}** — {value}" for label, value in fields.items()]
    report = "# SystemScope specification report\n\n" + "\n".join(lines) + "\n"
    source = fields["Data source"]
    filename = "demo-report.md" if source == "Sample replay" else "live-report.md"
    st.download_button("Download specification report", report, file_name=filename,
                       mime="text/markdown", on_click="ignore")


def dashboard(frame, specs, source):
    latest = frame.iloc[-1]
    seconds = latest["elapsed_s"]
    cpu = f"{latest['cpu_pct']:.0f}%"
    ram_gib = latest["ram_available_gib"]
    disk_gib = latest["disk_free_gib"]
    ram_status, ram_detail = capacity(ram_gib, latest["ram_total_gib"])
    disk_status, disk_detail = capacity(disk_gib, latest["disk_total_gib"])

    st.caption(f"{source} · {seconds:g} seconds · {len(frame)} readings in view")
    cpu_card, ram_card, disk_card = st.columns(3)
    cpu_card.metric("CPU used", cpu)
    ram_card.metric("RAM available", f"{ram_gib:.1f} GiB")
    disk_value = "Unavailable" if pd.isna(disk_gib) else f"{disk_gib:.1f} GiB"
    disk_card.metric("Windows drive free", disk_value)

    for label, status, detail in [
        ("Memory", ram_status, ram_detail),
        ("Storage", disk_status, disk_detail),
    ]:
        message = f"{label} — {status} · {detail}"
        if status == "Low":
            st.warning(message)
        else:
            st.write(message)

    chart = pd.DataFrame({
        "Elapsed seconds": frame["elapsed_s"],
        "CPU used (%)": frame["cpu_pct"],
        "RAM used (%)": 100 * (1 - frame["ram_available_gib"] / frame["ram_total_gib"]),
    })
    st.line_chart(chart, x="Elapsed seconds", y=["CPU used (%)", "RAM used (%)"],
                  y_label="Usage (%)")

    fields = {
        "Data source": source,
        "Elapsed time": f"{seconds:g} s",
        **specs,
        "CPU used": cpu,
        "RAM available / usable total": f"{ram_status} · {ram_detail}",
        "Windows drive free / capacity": f"{disk_status} · {disk_detail}",
        "Peak RAM used in this chart": f"{chart['RAM used (%)'].max():.1f}%",
        "Warning rule": f"Below {LOW_PERCENT}% available RAM or free drive space",
    }
    show_details(fields)


@st.fragment(run_every="2s")
def live_view():
    if "live_history" not in st.session_state:
        st.session_state.live_history = deque(maxlen=60)
        st.session_state.start_time = monotonic()

    row = read_live()
    row["elapsed_s"] = round(monotonic() - st.session_state.start_time, 1)
    st.session_state.live_history.append(row)
    frame = pd.DataFrame(list(st.session_state.live_history))
    dashboard(frame, computer_details(), "Live laptop")

mode = st.radio("Data source", ["Sample replay", "Live laptop"], horizontal=True)
if mode == "Live laptop":
    live_view()
else:
    st.session_state.pop("live_history", None)
    sample_path = Path(__file__).parent / "examples" / "memory-replay.csv"
    samples = pd.read_csv(sample_path)
    second = st.select_slider("Replay time (seconds)",
                              options=samples["elapsed_s"].tolist(), value=4)
    visible = samples.loc[samples["elapsed_s"] <= second]
    example_specs = {
        "CPU": "Example processor",
        "Logical processors": 4,
        "Operating system and build": "Windows (simulated device)",
    }
    dashboard(visible, example_specs, "Sample replay")