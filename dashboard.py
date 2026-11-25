"""Run from the SystemScope folder with python -m streamlit run dashboard.py."""

import csv
from collections import deque
from pathlib import Path
from time import monotonic

import streamlit as st
from streamlit.components.v1 import declare_component

from monitor import LOW_PERCENT, capacity, computer_details, read_live

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "examples" / "memory-replay.csv"
HISTORY_LIMIT = 60

st.set_page_config(page_title="SystemScope", layout="wide")
viewer = declare_component("systemscope_view", path=str(ROOT / "ui"))


def with_status(row):
    """Apply the same warning rules as the original monitor."""
    return {
        **row,
        "ram_status": capacity(row["ram_available_gib"], row["ram_total_gib"])[0],
        "disk_status": capacity(row["disk_free_gib"], row["disk_total_gib"])[0],
    }


def sample_rows():
    with SAMPLES.open(encoding="utf-8-sig", newline="") as file:
        return [
            with_status({key: float(value) for key, value in row.items()})
            for row in csv.DictReader(file)
        ]


source_control, pause_control = st.columns([2, 1], vertical_alignment="bottom")
source = source_control.radio("Data source", ["Sample replay", "Live laptop"], horizontal=True)
is_live = source == "Live laptop"
paused = pause_control.toggle("Pause live readings") if is_live else False

if not is_live:
    st.session_state.pop("scope_history", None)
    st.session_state.pop("scope_start", None)


@st.fragment(run_every=2 if is_live and not paused else None)
def show_dashboard():
    if is_live:
        if "scope_history" not in st.session_state:
            st.session_state.scope_history = deque(maxlen=HISTORY_LIMIT)
            st.session_state.scope_start = monotonic()
        history = st.session_state.scope_history
        if not paused or not history:
            row = read_live()
            row["elapsed_s"] = round(monotonic() - st.session_state.scope_start, 1)
            history.append(with_status(row))
        rows = list(history)
        specs = computer_details()
    else:
        rows = sample_rows()
        specs = {
            "CPU": "Example processor",
            "Logical processors": 4,
            "Operating system and build": "Windows (simulated device)",
        }

    viewer(rows=rows, specs=specs, mode=source, paused=paused, threshold=LOW_PERCENT,
           key="systemscope_viewer", default=None)


show_dashboard()
