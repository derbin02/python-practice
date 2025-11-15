# app.py
from __future__ import annotations
from pathlib import Path
import io
from typing import List, Dict, Tuple

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ---------- Helpers (settlement) ----------
def settle_balances(balances: Dict[str, float]) -> List[Tuple[str, str, float]]:
    creditors = [(n, round(a, 2)) for n, a in balances.items() if a > 0.005]
    debtors = [(n, round(-a, 2)) for n, a in balances.items() if a < -0.005]
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    txns = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        dname, damt = debtors[i]
        cname, camt = creditors[j]
        pay = min(damt, camt)
        txns.append((dname, cname, round(pay, 2)))
        damt -= pay
        camt -= pay
        if damt <= 0.005:
            i += 1
        else:
            debtors[i] = (dname, round(damt, 2))
        if camt <= 0.005:
            j += 1
        else:
            creditors[j] = (cname, round(camt, 2))
    return txns

def df_from_people(people: List[dict]) -> pd.DataFrame:
    return pd.DataFrame(people)

def csv_bytes_from_df(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def html_escape(s: str) -> str:
    """Very small HTML escaper for insertion into modal HTML."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#x27;"))

# ---------- App setup ----------
st.set_page_config(page_title="Expense Splitter", page_icon="💰", layout="centered")
# load css
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Center wrapper start
st.markdown('<div class="site-container">', unsafe_allow_html=True)

# ---------- Heading ----------
st.markdown("""
<div class="hero">
  <div class="title">Expense Splitter</div>
  <div class="subtitle">Split bills simply — add cost, assign people, finalize & pay</div>
</div>
""", unsafe_allow_html=True)

# ---------- Stepper UI (3 steps) ----------
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "people" not in st.session_state:
    st.session_state["people"] = []

# step bar
st.markdown("""
<div class="steps">
  <div class="step {s1}">1. Add cost</div>
  <div class="step {s2}">2. Assign people</div>
  <div class="step {s3}">3. Finalize</div>
</div>
""".format(s1="active" if st.session_state["step"]==1 else "",
           s2="active" if st.session_state["step"]==2 else "",
           s3="active" if st.session_state["step"]==3 else ""), unsafe_allow_html=True)

# ---------- Step 1: Add cost ----------
if st.session_state["step"] == 1:
    st.header("Step 1 — Enter total cost")
    col1, col2 = st.columns([2,1])
    with col1:
        total_amount = st.number_input("Total bill amount (₹)", min_value=0.0, value=1200.0, step=1.0, format="%.2f")
        people_count = st.number_input("Number of people", min_value=1, value=4, step=1)
    with col2:
        if st.button("Next → Assign people", key="to_step2"):
            st.session_state["total_amount"] = float(total_amount)
            st.session_state["people_count"] = int(people_count)
            if len(st.session_state["people"]) < st.session_state["people_count"]:
                for i in range(st.session_state["people_count"] - len(st.session_state["people"])):
                    st.session_state["people"].append({"name": f"Person {len(st.session_state['people'])+1}", "paid": 0.0, "upi": ""})
            st.session_state["step"] = 2

# ---------- Step 2: Assign people ----------
if st.session_state["step"] == 2:
    st.header("Step 2 — Add names and who paid what")
    st.write("Add each person's name, how much they paid, and optional UPI (for quick pay).")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Add person", key="add_person"):
            st.session_state["people"].append({"name": f"Person {len(st.session_state['people'])+1}", "paid": 0.0, "upi": ""})
    with c2:
        if st.button("Auto-fill to count", key="autofill_people"):
            cnt = st.session_state.get("people_count", 1)
            cur = len(st.session_state["people"])
            for i in range(cnt - cur):
                st.session_state["people"].append({"name": f"Person {cur + i + 1}", "paid": 0.0, "upi": ""})
    with c3:
        if st.button("Back ←", key="back_to_cost"):
            st.session_state["step"] = 1

    new_people = []
    for i, p in enumerate(st.session_state["people"]):
        cols = st.columns([4,2,3,1])
        name = cols[0].text_input(f"Name {i+1}", value=p.get("name",""), key=f"name_{i}")
        paid = cols[1].number_input(f"Paid {i+1}", min_value=0.0, value=float(p.get("paid",0.0)), format="%.2f", key=f"paid_{i}")
        upi = cols[2].text_input(f"UPI {i+1}", value=p.get("upi",""), placeholder="name@bank", key=f"upi_{i}")
        remove = cols[3].button("Remove", key=f"rem_{i}")
        if remove:
            continue
        new_people.append({"name": name.strip() or f"Person {i+1}", "paid": float(paid), "upi": upi.strip()})
    st.session_state["people"] = new_people

    st.markdown("### Preview")
    st.dataframe(pd.DataFrame(st.session_state["people"]).rename(columns={"paid":"Paid (₹)"}), use_container_width=True)

    if st.button("Next → Finalize", key="to_finalize"):
        st.session_state["step"] = 3

# ---------- Step 3: Finalize & show settlements ----------
if st.session_state["step"] == 3:
    st.header("Step 3 — Finalize & Who pays whom")
    total_amount = st.session_state.get("total_amount", 0.0)
    n = max(1, int(st.session_state.get("people_count", max(1, len(st.session_state["people"])))))
    people = st.session_state.get("people", [])

    if not people:
        st.info("No people added. Go back and add people first.")
        if st.button("Back ← Assign people"):
            st.session_state["step"] = 2
    else:
        df = df_from_people(people)
        df["paid"] = pd.to_numeric(df["paid"], errors="coerce").fillna(0.0)
        share = round(total_amount / n, 2)
        df["share"] = share
        df["balance"] = (df["paid"] - df["share"]).round(2)
        st.markdown(f"**Total bill:** ₹{total_amount:.2f}  •  **Each share:** ₹{share:.2f}")

        # Per-person cards (bigger center)
        st.markdown("<div class='cards-centered'>", unsafe_allow_html=True)
        for _, row in df.iterrows():
            name = row["name"]
            bal = float(row["balance"])
            if bal > 0.009:
                badge = f"Gets back ₹{bal:.2f}"
                cls = "card get"
            elif bal < -0.009:
                badge = f"Owes ₹{abs(bal):.2f}"
                cls = "card owe"
            else:
                badge = "Settled"
                cls = "card settled"
            upi = row.get("upi", "")
            st.markdown(f"""
            <div class="{cls}">
              <div class="card-left"><div class="initial">{name[:1].upper()}</div></div>
              <div class="card-mid">
                <div class="pname">{name}</div>
                <div class="pupi">{upi}</div>
              </div>
              <div class="card-right"><div class="badge">{badge}</div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Settlement transactions
        balances = dict(zip(df["name"], df["balance"]))
        txns = settle_balances(balances)
        st.markdown("### Suggested transactions")
        if not txns:
            st.success("All clear — no transfers needed.")
        else:
            for i, (payer, receiver, amt) in enumerate(txns, start=1):
                receiver_upi = ""
                for r in people:
                    if r["name"] == receiver:
                        receiver_upi = r.get("upi","")
                if receiver_upi:
                    text = f"Pay ₹{amt:.2f} to {receiver} ({receiver_upi}) for group split"
                else:
                    text = f"Pay ₹{amt:.2f} to {receiver} for group split"
                st.markdown(f"""
                <div class="txn">
                  <div class="txn-left">• <b>{payer}</b> ➜ <b>{receiver}</b> : ₹{amt:.2f}</div>
                  <div class="txn-right">
                    <button class="copy-btn" data-t="{text}">Copy</button>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            # copy button JS
            js = """
            <script>
            const streamlitDoc = window.parent.document;
            const buttons = streamlitDoc.querySelectorAll('.copy-btn');
            buttons.forEach(b=>{
              b.onclick = ()=>{
                const t = b.getAttribute('data-t');
                navigator.clipboard.writeText(t).then(()=>{
                  b.innerText = 'Copied ✓';
                  setTimeout(()=> b.innerText = 'Copy', 1200);
                }).catch(()=> alert('Copy failed; select text manually.'));
              };
            });
            </script>
            """
            components.html(js, height=0)

        # CSV
        csvb = csv_bytes_from_df(df)
        st.download_button("⬇️ Download summary CSV", data=csvb, file_name="split_summary.csv", mime="text/csv")

        # coin container (used by popup)
        st.markdown('<div class="coins-container" id="coins"><div class="coin c1"></div><div class="coin c2"></div><div class="coin c3"></div><div class="coin c4"></div><div class="coin c5"></div></div>', unsafe_allow_html=True)

       


    if st.button("Back ← Assign people", key="back_from_finalize"):
        st.session_state["step"] = 2

# Close center wrapper
st.markdown('</div>', unsafe_allow_html=True)
