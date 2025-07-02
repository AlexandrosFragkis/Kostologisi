try:
    import streamlit as st
except ModuleNotFoundError:
    raise ImportError("Το Streamlit δεν είναι εγκατεστημένο. Εκτέλεσε 'pip install streamlit' για να συνεχίσεις.")

import json
import os
import pandas as pd
from io import BytesIO
from docx import Document

st.set_page_config(layout="wide")

# --- Αρχεία για αποθήκευση τιμών ---
PRICE_FILE = "material_prices.json"

# --- Προεπιλεγμένες Τιμές Υλικών για Κοστολόγηση ---
def_material_prices = {
    "Καπλαμάς/Μελαμίνη": 130,
    "Λάκα/Μελαμίνη": 95,
    "Μελαμίνη/Μελαμίνη": 60,
    "Duropal": 85,
    "Compact": 100,
    "Corian": 300,
    "Εξαρτήματα Επίπλων": 150
}

# --- Σταθερή Λίστα Υλικών για Αναφορά ---
def_material_reference = {
    "Καπλαμάς Δρυς": 130,
    "Καπλαμάς Δρυς με ταμπλά": 140,
    "Καπλαμάς Δρυς με πηχάκια": 145,
    "Καπλαμάς Καρυδιά": 135,
    "Καπλαμάς Καρυδιά με ταμπλά": 145,
    "Καπλαμάς Καρυδιά με πηχάκια": 150,
    "MDF Λάκα": 95,
    "MDF Λάκα με ταμπλά": 105,
    "MDF Λάκα με πηχάκια": 110,
    "MDF Άβαφο": 70,
    "Κόντρα Πλακέ Λάκα": 100,
    "Κόντρα Πλακέ Άβαφο": 80,
    "Μελαμίνη": 60,
    "Duropal": 85,
    "Compact": 100,
    "Corian": 300,
    "Εξαρτήματα Επίπλων": 150
}

# --- Αποθήκευση / Φόρτωση ---
def load_prices():
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return def_material_prices.copy()

def save_prices(prices):
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

if "material_prices" not in st.session_state:
    st.session_state.material_prices = load_prices()
if "material_reference_prices" not in st.session_state:
    st.session_state.material_reference_prices = def_material_reference.copy()
if "furniture_list" not in st.session_state:
    st.session_state.furniture_list = []

# --- Sidebar: Ρυθμίσεις Υλικών ---
st.sidebar.header("🔧 Τιμές Υλικών")
with st.sidebar:
    st.subheader("Τιμές Υλικών Κοστολόγησης (€ / m² ή τεμ)")
    updated_prices = {}
    for mat in def_material_prices:
        val = st.number_input(f"{mat}", value=float(st.session_state.material_prices.get(mat, def_material_prices[mat])), min_value=0.0, key=f"price_{mat}")
        updated_prices[mat] = val
    if updated_prices != st.session_state.material_prices:
        st.session_state.material_prices = updated_prices
        save_prices(updated_prices)

    st.subheader("Τιμές Αναφοράς Υλικών")
    st.subheader("Ντουλάπα ανοιγόμενη από 1,6μ. εώς 4 συρτάρια (Εσωτερικά μελαμίνη)")
    for mat in def_material_reference:
        st.session_state.material_reference_prices[mat] = st.number_input(
            f"{mat} (αναφορά)",
            value=float(st.session_state.material_reference_prices.get(mat, def_material_reference[mat])),
            min_value=0.0,
            key=f"ref_{mat}"
        )
    st.subheader("Ντουλάπα ανοιγόμενη από 1,6μ. εώς 4 συρτάρια (Εσωτερικά μελαμίνη)")
  
# --- Κύριο Περιεχόμενο ---
st.title("📐 Κοστολόγηση Custom Επίπλων")

st.header("1. Εισαγωγή Διαστάσεων Κατασκευής (σε εκατοστά)")
construction_name = st.text_input("Όνομα Κατασκευής")
exterior_length = st.number_input("Μήκος εξωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0)
exterior_height = st.number_input("Ύψος εξωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0)
interior_length = st.number_input("Μήκος εσωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0)
interior_height = st.number_input("Ύψος εσωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0)

exterior_area = round((exterior_length * exterior_height) / 10000, 2)
interior_area = round((interior_length * interior_height) / 10000, 2)

st.header("2. Επιλογή Υλικών")
material_keys = list(st.session_state.material_prices.keys())
exterior_material = st.selectbox("Υλικό εξωτερικά", options=material_keys)
interior_material = st.selectbox("Υλικό εσωτερικά", options=material_keys)
panel_material = st.selectbox("Υλικό Πάγκου (κουζίνα/μπάνιο)", options=["Τίποτα", "Compact", "Corian", "Duropal"])
add_hardware = st.selectbox("Προσθήκη Εξαρτημάτων Επίπλου", options=["ΟΧΙ", "ΝΑΙ"])

st.header("3. Συρτάρια")
drawer_count = st.number_input("Αριθμός συρταριών", min_value=0, step=1)
drawer_price = 250

if st.button("Προσθήκη Επίπλου"):
    prices = st.session_state.material_prices
    exterior_cost = exterior_area * prices.get(exterior_material, 0)
    interior_cost = interior_area * prices.get(interior_material, 0)
    drawers_cost = drawer_count * drawer_price
    panel_cost = 0 if panel_material == "Τίποτα" else prices.get(panel_material, 0)
    hardware_cost = prices["Εξαρτήματα Επίπλων"] if add_hardware == "ΝΑΙ" else 0
    total_cost = exterior_cost + interior_cost + drawers_cost + panel_cost + hardware_cost

    st.session_state.furniture_list.append({
        "Κατασκευή": construction_name,
        "Εξωτερική επιφάνεια (m²)": exterior_area,
        "Εσωτερική επιφάνεια (m²)": interior_area,
        "Εξωτερικό υλικό": exterior_material,
        "Εσωτερικό υλικό": interior_material,
        "Πάγκος": panel_material,
        "Εξαρτήματα": add_hardware,
        "Συρτάρια": drawer_count,
        "Κόστος εξωτερικών": exterior_cost,
        "Κόστος εσωτερικών": interior_cost,
        "Κόστος συρταριών": drawers_cost,
        "Κόστος πάγκου": panel_cost,
        "Κόστος εξαρτημάτων": hardware_cost,
        "Σύνολο": total_cost
    })
    st.success("✅ Προστέθηκε έπιπλο στη λίστα")

# --- Προβολή Λίστας Επίπλων ---
if st.session_state.furniture_list:
    st.subheader("📋 Λίστα Επίπλων")
    df = pd.DataFrame(st.session_state.furniture_list)
    st.dataframe(df, use_container_width=True)

    total = df["Σύνολο"].sum()
    st.success(f"💰 Συνολικό Κόστος Όλων των Επίπλων: {total:.2f} €")

    if st.button("Επαναφορά Λίστας"):
        st.session_state.furniture_list = []
        st.rerun()

    # --- Εξαγωγή σε Word ---
    doc = Document()
    doc.add_heading("Λίστα Επίπλων", level=1)
    for item in st.session_state.furniture_list:
        for k, v in item.items():
            doc.add_paragraph(f"{k}: {v}")
        doc.add_paragraph("---")

    word_buffer = BytesIO()
    doc.save(word_buffer)
    word_buffer.seek(0)

    st.download_button(
        label="📥 Λήψη Λίστας σε Word",
        data=word_buffer,
        file_name="lista_epiplon.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# --- Επιπλέον Υπολογισμοί ---
st.header("4. Επιπλέον Υπολογισμοί")
manual_cost = st.number_input("Χειροκίνητο συνολικό κόστος κατασκευής (€)", min_value=0.0, step=10.0)
commission_percent = st.number_input("Ποσοστό προμήθειας αρχιτέκτονα (%)", min_value=0.0, max_value=100.0, step=1.0)
commission_amount = manual_cost * (commission_percent / 100)
final_cost = manual_cost + commission_amount

st.write(f"🔧 Προμήθεια ({commission_percent:.0f}%): {commission_amount:.2f} €")
if manual_cost > 0:
    st.success(f"🏁 Τελικό Κόστος με Προμήθεια: {final_cost:.2f} €")
