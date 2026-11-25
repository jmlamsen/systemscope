# SystemScope — Five-day build guide

Build a Windows dashboard that shows your computer’s hardware, charts CPU and RAM use, warns about low memory or storage, and downloads a report. Work from top to bottom. Each day ends with a result you can check on your laptop.

| Day | Time | What you can do by the end |
| --- | ---: | --- |
| [1. Set up the project](#day-1-set-up-the-project) | 1 hour | Open a local Streamlit example in your browser. |
| [2. Read your laptop](#day-2-read-your-laptop) | 2 hours | Print your CPU, RAM, and Windows drive readings and compare them with Windows. |
| [3. Build the live dashboard](#day-3-build-the-live-dashboard) | 2 hours | Watch two chart lines update and see a warning when space is low. |
| [4. Add replay and export](#day-4-add-replay-and-export) | 3 hours | Reproduce a memory warning, watch it clear, and save the evidence. |
| [5. Test and publish](#day-5-test-and-publish) | 2 hours | Run three tests and publish a README with a demo image and a sample report. |

**Allow about 10 hours in total.** Use PowerShell for command blocks and your text editor for file contents. On Days 2–5, open PowerShell inside the same `SystemScope` folder. If you already started the project, resume at the first daily checkpoint you still need.

## Day 1. Set up the project

**1. Choose a drive.** Your Intel Core i3-1005G1 laptop has 12 GB RAM. You reported **14 GB free on the 117 GB Windows drive**, about 12%. Allow roughly 2 GB for setup as an estimate. Open PowerShell and run the two lines below. The first gives the Windows drive letter. Write down its free space from the second line. If another drive has more room, open a folder on that drive for the project. SystemScope will still measure the drive containing Windows.

~~~powershell
$env:SystemDrive
Get-PSDrive -PSProvider FileSystem
~~~

**2. Create the folder and Python environment.** Open the parent folder in File Explorer, type `powershell` in the address bar, and press Enter. These commands use **64-bit Python 3.12**. If you have Python 3.13, use `py -3.13` in both Python commands. If your computer recognizes `python`, check `python --version` and use `python -m venv .venv` with either version. For a new installation, choose 64-bit Python 3.13 for Windows. [Python for Windows](https://www.python.org/downloads/windows/)

~~~powershell
py -3.12 --version
mkdir SystemScope
cd SystemScope
py -3.12 -m venv .venv
mkdir examples
mkdir docs
~~~

**3. Install the three packages.** Run the following commands once. `.venv` is this project’s private Python environment. The first command avoids keeping downloaded packages in pip’s cache. The last command records the installed versions so another person can repeat your setup. [Streamlit setup](https://docs.streamlit.io/get-started/installation/command-line) · [pip cache options](https://pip.pypa.io/en/stable/topics/caching/)

~~~powershell
.\.venv\Scripts\python.exe -m pip install --no-cache-dir "streamlit>=1.50,<2" "psutil>=7.2,<8" "pandas>=2.2.3,<4"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding ascii requirements.txt
~~~

**4. Create `.gitignore`** in the project folder. Paste these four lines. Git will skip the local Python environment, temporary Python files, and live reports. If you use Notepad, select **All files** under **Save as type** so each filename keeps its proper ending.

~~~gitignore
.venv/
__pycache__/
*.pyc
live-report*.md
~~~

**Day 1 checkpoint.** Run the command below. The Streamlit example should open in your browser, and `requirements.txt` should contain package names and versions. If the browser stays closed, open the local address shown in PowerShell. Return to PowerShell and press **Ctrl+C** to stop the example. [Streamlit example command](https://docs.streamlit.io/develop/api-reference/cli/hello)

~~~powershell
.\.venv\Scripts\python.exe -m streamlit hello --server.address=127.0.0.1
~~~

## Day 2. Read your laptop

**1. Create `monitor.py`** beside `requirements.txt`. The file does three jobs. `computer_details()` gets the CPU name and Windows build. `read_live()` takes one reading. `capacity()` works out how much is available and returns **Low** below 15%, **OK** at or above 15%, or **Unavailable** for a missing reading. The capacities are in GiB, where one GiB is 1,024³ bytes. [psutil reference](https://psutil.readthedocs.io/stable/)

~~~python
import os
import platform
from functools import lru_cache

import pandas as pd
import psutil

GIB = 1024 ** 3
LOW_PERCENT = 15


def capacity(remaining, total):
    if pd.isna(remaining) or pd.isna(total) or total <= 0:
        return "Unavailable", "Reading unavailable"
    percent = 100 * remaining / total
    status = "Low" if percent < LOW_PERCENT else "OK"
    detail = f"{remaining:.1f} of {total:.1f} GiB ({percent:.1f}%)"
    return status, detail


@lru_cache(maxsize=1)
def computer_details():
    cpu_name = platform.processor() or "Unavailable"
    if platform.system() == "Windows":
        import winreg

        key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            cpu_name = name.strip() or cpu_name
        except OSError:
            pass  # The processor identifier above is still usable.

    return {
        "CPU": cpu_name,
        "Logical processors": psutil.cpu_count(logical=True) or "Unavailable",
        "Operating system and build": f"{platform.system()} {platform.version()}",
    }


def read_live():
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    try:
        drive = psutil.disk_usage(os.environ["SystemRoot"])
    except (KeyError, OSError):
        drive = None

    return {
        "cpu_pct": cpu,
        "ram_available_gib": ram.available / GIB,
        "ram_total_gib": ram.total / GIB,
        "disk_free_gib": drive.free / GIB if drive else None,
        "disk_total_gib": drive.total / GIB if drive else None,
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(computer_details())
    reading = read_live()
    pprint(reading)
    status, detail = capacity(reading["disk_free_gib"], reading["disk_total_gib"])
    print(f"Windows drive — {status} · {detail}")
~~~

**2. Take a real reading.** Save the file and run it from the project folder.

~~~powershell
.\.venv\Scripts\python.exe monitor.py
~~~

**Day 2 checkpoint.** Open **Task Manager → Performance** and compare the CPU name and memory figures. Open **File Explorer → This PC** and compare the free space on the Windows drive. If the drive still has about 14 of 117 GB available, the final line should say **Low**. CPU use and available RAM can change while you compare them. Write down one pair of drive readings for your README.

## Day 3. Build the live dashboard

**1. Create `app.py`** beside `monitor.py`. Paste the whole block. The app keeps up to 60 readings in memory. A new reading replaces the oldest once the chart is full. The chart shows RAM **used**, while the card shows RAM **available**. [Streamlit timed refresh](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)

~~~python
from collections import deque
from time import monotonic

import pandas as pd
import streamlit as st

from monitor import LOW_PERCENT, capacity, computer_details, read_live

st.set_page_config(page_title="SystemScope", layout="wide")
st.title("SystemScope")


def show_details(fields):
    table = pd.DataFrame(list(fields.items()), columns=["Item", "Reading"])
    with st.expander("Computer details"):
        st.table(table.astype(str))


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


live_view()
~~~

**2. Start your dashboard.** Run this command from the project folder. Use it again on Days 4 and 5. Leave PowerShell open while viewing the page.

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1
~~~

**Day 3 checkpoint.** After a few seconds, look for three cards and two chart lines. Open **Computer details** and find your CPU name and drive capacity. Keep the tab active for just over two minutes. The elapsed time should keep increasing while the count stops at **60 readings**. Press **Ctrl+C** in PowerShell before editing the app on Day 4.

## Day 4. Add replay and export

You can split today into two sessions. First make the case replay in the dashboard. Then add the download button and collect the two files for GitHub.

### Session A. Make the same case work every time

**1. Create `examples/memory-replay.csv`.** Save these six simulated readings exactly as shown. The drive stays at 14 of 117 GiB free throughout the case.

~~~csv
elapsed_s,cpu_pct,ram_available_gib,ram_total_gib,disk_free_gib,disk_total_gib
0,18,4.8,12,14,117
2,35,2.4,12,14,117
4,62,1.2,12,14,117
6,43,0.9,12,14,117
8,23,2.4,12,14,117
10,16,4.8,12,14,117
~~~

**2. Add this import** near the top of `app.py`, just after `from collections import deque`.

~~~python
from pathlib import Path
~~~

**3. Find the single `live_view()` call on the very last line of `app.py`.** Replace that line with the block below. The `def live_view():` function above it is the function the new menu calls.

~~~python
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
~~~

Start the dashboard with the Day 3 command. It opens in **Sample replay** at 4 seconds. Move the slider and check each result.

| Replay time | RAM available | Expected warnings |
| ---: | ---: | --- |
| 0 seconds | 4.8 of 12 GiB (40%) | Low storage |
| 4 seconds | 1.2 of 12 GiB (10%) | Low memory and low storage |
| 8 seconds | 2.4 of 12 GiB (20%) | Low storage. The memory warning has cleared. |

Switch to **Live laptop** and check that your real CPU name returns in **Computer details**. Switch back to **Sample replay**. If the CSV fails to load, open a second PowerShell window in `SystemScope` and run `Test-Path .\examples\memory-replay.csv`. It should return `True`. If it returns `False`, check the folder name and file extension.

### Session B. Save the evidence

**4. Add the report download.** Stop the app with **Ctrl+C**. In `app.py`, find the function that starts with `def show_details(fields):`, just above `def dashboard(frame, specs, source):`. Replace the entire `show_details` function with this version, then save and run the Day 3 command again. The download and details table use the same values. [Streamlit download button](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)

~~~python
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
~~~

**5. Collect two files.** At **4 seconds**, capture the dashboard using Windows Snipping Tool. Save the image as `docs/demo.png`. Then move the slider to **8 seconds**, click **Download specification report**, and move `demo-report.md` from your downloads into `examples`.

**Day 4 checkpoint.** Open `examples/demo-report.md`. It should say **Sample replay**, **8 s**, **2.4 of 12.0 GiB** RAM available, and **14.0 of 117.0 GiB** drive space free. The report should also show **92.5% peak RAM used**. That peak happened at 6 seconds, when only 0.9 of 12 GiB was available.

## Day 5. Test and publish

**1. Create `test_monitor.py`** beside `monitor.py`. These three tests check the exact warning boundary, your example drive size, and a missing drive reading.

~~~python
import unittest

from monitor import capacity


class WarningTests(unittest.TestCase):
    def test_memory_cutoff(self):
        self.assertEqual(capacity(1.8, 12)[0], "OK")
        self.assertEqual(capacity(1.79, 12)[0], "Low")

    def test_target_drive(self):
        self.assertEqual(capacity(14, 117)[0], "Low")

    def test_missing_drive(self):
        self.assertEqual(capacity(None, None)[0], "Unavailable")
~~~

Run them from the project folder. The last lines should say `Ran 3 tests` and `OK`.

~~~powershell
.\.venv\Scripts\python.exe -m unittest -v test_monitor
~~~

**2. Measure the installation.** In PowerShell, run these lines. Record the environment size in MiB and the free space shown for the Windows drive. The environment size counts files inside `.venv`. The before-and-after drive readings also include any other activity on your laptop.

~~~powershell
$venvBytes = (Get-ChildItem .venv -Recurse -Force -File | Measure-Object Length -Sum).Sum
[math]::Round($venvBytes / 1MB, 1)
Get-PSDrive -PSProvider FileSystem
~~~

**3. Create `README.md`.** Paste this starting text. Fill in the blanks with your measured values and the observation from Day 2. If you built with Python 3.13, use that version in the README's example command. Put this build guide in `docs/SystemScope-Daily-Build-Guide.md` so the link works.

~~~markdown
# SystemScope

This laptop shows two warnings. Which one clears by 8 seconds?

![Sample replay at 4 seconds showing low memory and low storage](docs/demo.png)

[Open the report from 8 seconds](examples/demo-report.md)

At 4 seconds, only 10% of RAM is available. By 8 seconds it recovers to 20%.
The Windows drive stays about 12% free, so its storage warning stays on.

## Run on Windows

Open PowerShell in the downloaded project folder. These commands use 64-bit Python 3.12.
If you have 3.13, use `py -3.13` in the first command.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v test_monitor
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1
```

Choose **Sample replay** to explore the case or **Live laptop** to read the computer running the app.

## Laptop check

- Python environment size on my laptop — ___ MiB.
- Windows drive free during my check — SystemScope showed ___ GiB. File Explorer showed ___.
- One thing I noticed when comparing the readings — ___.

[Follow the five-day build guide](docs/SystemScope-Daily-Build-Guide.md)
~~~

**4. Publish the project.** On GitHub, create a repository called `systemscope`. For an empty repository, choose **uploading an existing file**. For one that already has a file, choose **Add file → Upload files**. Select the files listed below and drag the `docs` and `examples` folders with their contents. Commit the upload. Choosing just these files keeps the large `.venv` folder on your computer. [GitHub file uploads](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

| Location | Files to include |
| --- | --- |
| Top of the repository | `README.md`, `app.py`, `monitor.py`, `test_monitor.py`, `requirements.txt`, `.gitignore` |
| `examples/` | `memory-replay.csv`, `demo-report.md` |
| `docs/` | `demo.png`, `SystemScope-Daily-Build-Guide.md` |

**Day 5 checkpoint.** Open the repository as a visitor. The README should display the 4-second screenshot. Click the sample report and check that it opens at the 8-second result. A reviewer can now follow the case on GitHub or run it locally with the commands in the README.
