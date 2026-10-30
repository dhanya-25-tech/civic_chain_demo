
import json
from urllib.parse import urlparse

import requests
import streamlit as st


# ==========================================================
# 1. TINYFISH API KEY
# Paste your TinyFish API key here.
# Keep this file private. Do not upload it to GitHub.
# ==========================================================

TINYFISH_API_KEY = "sk-tinyfish-nyvPk6Tyou6KtA4t0CAE9_6Ms1Vd_Anz"

SEARCH_API = "https://api.search.tinyfish.ai"
AGENT_API = "https://agent.tinyfish.ai/v1/automation/run-sse"


# ==========================================================
# 2. STREAMLIT PAGE
# ==========================================================

st.set_page_config(
    page_title="CivicChain AI",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ CivicChain AI")
st.caption("Multi-Website Civic Investigation Powered by TinyFish")

st.markdown(
    """
    **Report a civic problem and investigate government websites.**

    CivicChain AI helps you discover:
    - Responsible government departments
    - Public repair projects and tenders
    - Official complaint portals
    - Escalation procedures
    """
)


# ==========================================================
# 3. SEARCH GOVERNMENT WEBSITES
# ==========================================================

def search_web(query):
    response = requests.get(
        SEARCH_API,
        params={"query": query},
        headers={"X-API-Key": TINYFISH_API_KEY},
        timeout=35
    )

    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict):
        results = data.get("results", data.get("data", []))

        if isinstance(results, dict):
            return results.get("results", [])

        if isinstance(results, list):
            return results

    return []


# ==========================================================
# 4. CHECK OFFICIAL GOVERNMENT WEBSITES
# ==========================================================

def official_candidate(url):
    try:
        host = (urlparse(url).hostname or "").lower()

        return (
            host.endswith(".gov.in")
            or host.endswith(".nic.in")
        )

    except Exception:
        return False


# ==========================================================
# 5. TINYFISH BROWSER AUTOMATION
# ==========================================================

def browser_research(url, goal, log):
    headers = {
        "X-API-Key": TINYFISH_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "url": url,
        "goal": goal,
        "browser_profile": "lite"
    }

    with requests.post(
        AGENT_API,
        headers=headers,
        json=payload,
        stream=True,
        timeout=(20, 360)
    ) as response:

        response.raise_for_status()

        completed_event = None

        for raw in response.iter_lines(decode_unicode=True):

            if not raw or not raw.startswith("data:"):
                continue

            try:
                event = json.loads(raw[5:].strip())
            except json.JSONDecodeError:
                continue

            event_type = str(
                event.get("type", "")
            ).upper()

            if event_type == "PROGRESS":
                log.write(
                    "🔄 " + str(
                        event.get("purpose", "Browsing website...")
                    )
                )

            elif event_type == "COMPLETE":
                completed_event = event

            elif event_type in ("ERROR", "FAILED"):
                raise RuntimeError(
                    str(event.get("error", "Browser automation failed"))
                )

        if not completed_event:
            raise RuntimeError(
                "TinyFish did not return a completion event."
            )

        status = str(
            completed_event.get("status", "")
        ).upper()

        if status != "COMPLETED":
            raise RuntimeError(
                str(
                    completed_event.get(
                        "error",
                        "Investigation was not completed."
                    )
                )
            )

        return completed_event.get(
            "resultJson",
            completed_event.get("result", {})
        )


# ==========================================================
# 6. FORMAT TINYFISH RESULTS
# ==========================================================

def clean_result(result):

    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"summary": result}

    if isinstance(result, dict):
        return result

    return {"summary": str(result)}


# ==========================================================
# 7. SIDEBAR - NO API KEY INPUT
# ==========================================================

with st.sidebar:

    st.header("⚙️ Investigation Settings")

    max_sites = st.slider(
        "Maximum websites to investigate",
        min_value=2,
        max_value=8,
        value=4
    )

    if (
        TINYFISH_API_KEY
        and TINYFISH_API_KEY
        != "PASTE_YOUR_NEW_TINYFISH_API_KEY_HERE"
    ):
        st.success("TinyFish API key configured")
    else:
        st.warning("Add your TinyFish API key in app.py")

    st.info(
        "TinyFish browser automation may use paid API credits. "
        "Start with 2 websites while testing."
    )


# ==========================================================
# 8. CITIZEN COMPLAINT FORM
# ==========================================================

st.subheader("📝 Report Your Civic Problem")

with st.form("issue_form"):

    col1, col2 = st.columns(2)

    with col1:
        city = st.text_input(
            "City",
            value="Bengaluru"
        )

    with col2:
        locality = st.text_input(
            "Locality / Landmark",
            value="Yelahanka"
        )

    category = st.selectbox(
        "Issue Type",
        [
            "Pothole / damaged road",
            "Water leakage",
            "Drainage / flooding",
            "Garbage",
            "Streetlight",
            "Road digging",
            "Other"
        ]
    )

    description = st.text_area(
        "Describe the Problem",
        value="A road near my area has been damaged for several weeks.",
        height=120
    )

    submitted = st.form_submit_button(
        "🔎 Investigate Civic Problem",
        type="primary",
        use_container_width=True
    )


# ==========================================================
# 9. MULTI-WEBSITE INVESTIGATION
# ==========================================================

if submitted:

    if (
        not TINYFISH_API_KEY
        or TINYFISH_API_KEY
        == "PASTE_YOUR_NEW_TINYFISH_API_KEY_HERE"
    ):
        st.error(
            "Please paste your TinyFish API key "
            "at the top of app.py."
        )
        st.stop()

    if not city.strip() or not locality.strip() or not description.strip():
        st.error(
            "Please enter the city, locality and problem description."
        )
        st.stop()

    missions = [
        (
            "Authority",
            f"{category} {locality} {city} "
            "responsible government department "
            "jurisdiction site:gov.in"
        ),
        (
            "Projects",
            f"{category} {locality} {city} "
            "repair project tender work order site:gov.in"
        ),
        (
            "Complaints",
            f"{category} {city} "
            "official government grievance portal site:gov.in"
        ),
        (
            "Escalation",
            f"{category} {city} "
            "grievance escalation citizen charter site:gov.in"
        )
    ]

    findings = []
    candidates = []
    seen_hosts = set()

    with st.status(
        "🔍 Discovering government websites...",
        expanded=True
    ) as status:

        # STEP A: Discover different websites

        for mission_name, query in missions:

            st.write(f"🔎 Searching for {mission_name} websites...")

            try:
                search_results = search_web(query)

            except Exception as error:
                st.warning(
                    f"{mission_name} search failed: {error}"
                )
                continue

            for result in search_results:

                if not isinstance(result, dict):
                    continue

                url = result.get("url", "")

                if isinstance(url, dict):
                    url = url.get("uri", "")

                if not isinstance(url, str):
                    continue

                host = urlparse(url).hostname or ""

                if (
                    url.startswith("https://")
                    and official_candidate(url)
                    and host not in seen_hosts
                ):

                    candidates.append({
                        "mission": mission_name,
                        "url": url,
                        "title": result.get("title", "")
                    })

                    seen_hosts.add(host)
                    break

        # STEP B: Check discovered websites

        if not candidates:
            status.update(
                label="No official websites discovered",
                state="error"
            )

            st.error(
                "No official government websites were found. "
                "Try another city, locality or problem description."
            )
            st.stop()

        st.write(
            f"🌐 Found {len(candidates)} distinct government websites."
        )

        # STEP C: Run TinyFish on each website

        for index, candidate in enumerate(
            candidates[:max_sites],
            start=1
        ):

            st.write(
                f"🌐 Investigating website {index}: "
                f"{candidate['url']}"
            )

            goal = f"""
            Investigate this government website for a civic issue.

            City: {city}
            Locality: {locality}
            Problem: {category}
            Description: {description}

            Research mission: {candidate['mission']}

            Browse relevant internal pages and follow useful links.

            Investigate:
            1. Responsible government department
            2. Relevant public repair projects
            3. Tender or work order information
            4. Official complaint portal
            5. Complaint escalation process

            Do not submit any forms.
            Do not log into any account.
            Do not invent information.

            Return a JSON object containing:

            summary
            responsible_agency
            project_details
            complaint_url
            escalation
            evidence_urls
            uncertainty

            If information is unavailable, use null or [].
            """

            try:

                result = browser_research(
                    candidate["url"],
                    goal,
                    st
                )

                findings.append({
                    **candidate,
                    "status": "completed",
                    "data": clean_result(result)
                })

                st.success(
                    f"Completed: {candidate['mission']}"
                )

            except Exception as error:

                findings.append({
                    **candidate,
                    "status": "failed",
                    "error": str(error)
                })

                st.warning(
                    f"Could not complete {candidate['mission']}: {error}"
                )

        status.update(
            label="Investigation finished",
            state="complete"
        )

    # Save investigation so results survive Streamlit reruns

    st.session_state["investigation"] = {
        "city": city,
        "locality": locality,
        "category": category,
        "description": description,
        "findings": findings
    }


# ==========================================================
# 10. INVESTIGATION REPORT
# ==========================================================

if "investigation" in st.session_state:

    data = st.session_state["investigation"]
    findings = data["findings"]

    completed = [
        finding
        for finding in findings
        if finding["status"] == "completed"
    ]

    st.divider()

    st.header("📊 Civic Investigation Report")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Websites Attempted",
        len(findings)
    )

    col2.metric(
        "Successful Investigations",
        len(completed)
    )

    col3.metric(
        "Failed Investigations",
        len(findings) - len(completed)
    )

    # Display individual website findings

    for finding in findings:

        success = finding["status"] == "completed"

        icon = "✅" if success else "⚠️"

        with st.expander(
            f"{icon} {finding['mission']} — {finding['url']}",
            expanded=True
        ):

            st.link_button(
                "🌐 Open Government Website",
                finding["url"]
            )

            if success:

                item = finding["data"]

                st.markdown("**Investigation Summary**")
                st.write(
                    item.get("summary")
                    or "No summary provided."
                )

                fields = [
                    "responsible_agency",
                    "project_details",
                    "complaint_url",
                    "escalation",
                    "uncertainty"
                ]

                for field in fields:

                    value = item.get(field)

                    if value:
                        st.markdown(
                            f"**{field.replace('_', ' ').title()}**"
                        )
                        st.write(value)

                evidence = item.get("evidence_urls")

                if evidence:
                    st.markdown("**Evidence Sources**")
                    st.write(evidence)

            else:
                st.error(finding["error"])

    st.info(
        "These are research findings, not independently verified facts. "
        "Review the official source links before relying on them."
    )

    # ======================================================
    # 11. COMPLAINT GENERATOR
    # ======================================================

    st.header("✍️ AI-Assisted Complaint Draft")

    agency_names = [
        str(finding["data"].get("responsible_agency"))
        for finding in completed
        if finding["data"].get("responsible_agency")
    ]

    agency = (
        agency_names[0]
        if agency_names
        else "Concerned Government Officer"
    )

    complaint = f"""To,
{agency}

Subject: Request for action regarding {data['category']} in {data['locality']}

Respected Sir/Madam,

I would like to report a civic issue in {data['locality']}, {data['city']}.

Issue Type: {data['category']}

Problem Description:
{data['description']}

I kindly request the concerned department to inspect
the location and take appropriate action.

Please provide a complaint reference number and
information about the follow-up procedure.

Thank you.

Yours faithfully,
Concerned Citizen
"""

    edited_complaint = st.text_area(
        "Review and edit your complaint",
        value=complaint,
        height=320
    )

    st.download_button(
        "📄 Download Complaint",
        data=edited_complaint,
        file_name="civic_complaint.txt",
        mime="text/plain"
    )

    # ======================================================
    # 12. DOWNLOAD FULL REPORT
    # ======================================================

    st.download_button(
        "⬇️ Download Investigation Report",
        data=json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        file_name="civicchain_investigation.json",
        mime="application/json"
    )

    st.success(
        "CivicChain AI investigation report is ready!"
    )
