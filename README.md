# CivicChain AI — Multi-Website TinyFish Demo

## Run

1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Launch:
   `streamlit run app.py`
5. Enter your TinyFish API key in the sidebar (or set `TINYFISH_API_KEY`).
6. Enter an issue and click **Investigate civic problem**.

## What it does

- Uses TinyFish Search to discover distinct official government domains.
- Launches separate TinyFish browser-agent tasks for jurisdiction, projects, complaints, and escalation.
- Displays each visited starting URL, actual browser progress, findings, and errors.
- Generates an editable complaint draft and downloadable investigation JSON.

## Notes

- This is a hackathon starter, not a production-grade jurisdiction-verification system.
- A government domain does not necessarily establish authority for a particular asset.
- Some searches will not find relevant government domains, and some browser runs may fail.
- Browser automation can incur charges. Test with 2 websites first.
- The dashboard counts attempted starting websites, not every internal page the browser may open.
- No complaints are submitted automatically.
