import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered"
)

# Load CSS
with open("styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Core logic
def calc_bmi(weight, height):
    h = height / 100
    return weight / (h * h)

def category(bmi):
    if bmi < 18.5:
        return "Underweight", "#ffb020"
    elif bmi < 25:
        return "Normal", "#06c167"
    elif bmi < 30:
        return "Overweight", "#ff7e20"
    else:
        return "Obese", "#e63939"

def export_csv(h, w, bmi, cat):
    df = pd.DataFrame([{
        "height_cm": h,
        "weight_kg": w,
        "bmi": round(bmi, 2),
        "category": cat
    }])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()

# ---------------------- UI ----------------------

# Hero Section
st.markdown("""
<div class="hero">
    <div class="hero-title">BMI Calculator</div>
    <div class="hero-sub">Instant, accurate & clean health metric evaluation</div>
</div>
""", unsafe_allow_html=True)

# Centered card
st.markdown("<div class='container'>", unsafe_allow_html=True)

col1, col2 = st.columns([1.1, 1], gap="large")

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Enter Your Details</div>", unsafe_allow_html=True)

    weight = st.number_input("Weight (kg)", min_value=1.0, max_value=250.0, value=70.0)
    height = st.number_input("Height (cm)", min_value=80.0, max_value=260.0, value=170.0)

    st.write("")
    if st.button("Calculate BMI", use_container_width=True):
        bmi = calc_bmi(weight, height)
        cat, color = category(bmi)
        st.session_state["bmi"] = bmi
        st.session_state["cat"] = cat
        st.session_state["col"] = color

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Your Results</div>", unsafe_allow_html=True)

    if "bmi" not in st.session_state:
        st.markdown("<div class='placeholder'>No data yet. Enter values & click Calculate.</div>", unsafe_allow_html=True)
    else:
        bmi = st.session_state["bmi"]
        cat = st.session_state["cat"]
        color = st.session_state["col"]

        st.markdown(
            f"""
            <div class='result-box'>
                <div class='bmi-value'>{bmi:.2f}</div>
                <div class='bmi-badge' style='background:{color}'>{cat}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        csv = export_csv(height, weight, bmi, cat)
        st.download_button("Download Result as CSV", data=csv, file_name="bmi_result.csv")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>BMI = weight (kg) / height (m²). Not a medical diagnosis.</div>", unsafe_allow_html=True)
