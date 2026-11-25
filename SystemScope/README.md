# SystemScope

SystemScope is a Windows dashboard that shows how busy your processor (CPU) is, how much memory (RAM) your apps can still use, and how much space is left on your Windows drive. You can watch your own laptop or explore a short sample in your browser.

## Try the demo

Download and unzip the project, then open `ui/index.html` in your browser. The demo works offline and uses six sample readings. You can try it before installing Python.

**Which warning clears when you move the slider from 4 to 8 seconds?**

| Replay time | Memory available | Windows drive free | What the dashboard shows |
| --- | --- | --- | --- |
| 4 seconds | 1.2 of 12 GiB (10%) | 14 of 117 GiB (about 12%) | Memory and storage both show **Low**. |
| 8 seconds | 2.4 of 12 GiB (20%) | 14 of 117 GiB (about 12%) | **Memory recovered** appears in the history. Storage is still **Low**. |

GiB is the unit used here for memory and drive space. The dashboard marks either one as **Low** when less than 15% is available. At 8 seconds, click **Export report**. The report gives a peak RAM use of **92.5%**. Move the slider back to **6 seconds** to see that peak on the chart.

## What’s on the screen

- **Three reading cards** show CPU load, available RAM, and free drive space. Each card has a large number. On wider screens, bars show how much CPU is in use and how much memory and drive space are left. The cards stack on small screens.
- **Usage history** draws CPU use as a solid green line and RAM use as a dashed gold line. The RAM card shows memory still available. The line shows memory already in use.
- **Status history** shows when a warning appears or clears. The memory and drive cards spell out **OK**, **Low**, or **Unavailable**, so you can read the status by name.
- **Computer details** expands to show the processor name, Windows version, total usable memory, and drive size.
- **Export report** saves the selected reading as `demo-report.md` in sample mode or `live-report.md` in live mode. You can open either file in a text editor.

## Run it on your Windows laptop

Open PowerShell in the folder that contains `dashboard.py`. You can keep the project on a second drive. It still checks the drive where Windows is installed.

**First-time setup.** These commands use 64-bit Python 3.12. If you have Python 3.13, use `py -3.13` on the first line. If you already set up this project’s `.venv` and packages, skip to **Start the dashboard**.

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir "streamlit>=1.50,<2" "psutil>=7.2,<8" "pandas>=2.2.3,<4"
~~~

**Start the dashboard.**

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.address=127.0.0.1
~~~

Open the local address shown in PowerShell and choose **Live laptop**. It takes a reading about every two seconds and keeps the latest 60 readings in memory. Choose **Pause live readings** to hold the chart, or press **Ctrl+C** in PowerShell to stop the app.

## How it works

`monitor.py` reads the laptop’s hardware using Python and psutil. `dashboard.py` runs the app with Streamlit. The screen uses HTML, CSS, and JavaScript to draw the cards and chart with the browser’s own tools.
