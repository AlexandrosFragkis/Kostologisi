try:
    import streamlit as st
except ModuleNotFoundError:
    raise ImportError("Το Streamlit δεν είναι εγκατεστημένο. Εκτέλεσε 'pip install streamlit' για να συνεχίσεις.")

import json
import os
import pandas as pd
from io import BytesIO
from docx import Document
from PIL import Image
import base64

st.set_page_config(layout="wide", page_title="Κοστολόγηση Επίπλων", page_icon="📐")

# --- Αρχεία για αποθήκευση τιμών ---
PRICE_FILE = "material_prices.json"

# --- Προεπιλεγμένες Τιμές Υλικών για Κοστολόγηση ---
def_material_prices = {
    "Καπλαμάς Δρυς": 130,
    "Λάκα": 95,
    "Μελαμίνη": 60,
    "Duropal": 85,
    "Compact": 100,
    "Corian": 300,
    "Εξαρτήματα Επίπλων": 150
}

# --- Τιμές Αναφοράς Επίπλων ---
def_furniture_reference = {
    "Ντουλάπα ανοιγόμενη": {
        "Μελαμίνη": 320,
        "Λάκα ματ/σατινέ": 400,
        "Λάκα ζαγρέ": 430,
        "Λάκα ματ/σατινέ με ταμπλά": 550,
        "Λάκα ματ/σατινέ με πηχάκια": 430,
        "Καπλαμάς δρυς": 430,
        "Καπλαμάς δρυς με ταμπλά": 580,
        "Καπλαμάς δρυς με πηχάκια": 460,
        "Καπλαμάς καρυδιά": 520,
        "Καπλαμάς καρυδιά με ταμπλα": 670,
        "Καπλαμάς καρυδιά με πηχάκια": 550,
        "Τζάμι με μεταλλικό πλαίσιο": 550
    },
    "Ντουλάπα συρόμενη": {
        "Μελαμίνη": 400,
        "Λάκα ματ/σατινέ": 480,
        "Λάκα ζαγρέ": 520,
        "Καπλαμάς δρυς": 550,
        "Καπλαμάς καρυδιά": 600,
        "Με καθρέπτη": 480,
        "Τζάμι με μεταλλικό πλαίσιο": 580
    },
    "Ντουλάπα ανοιγόμενη με ταπετσαρία": {
        "Λάκα ματ/σατινέ": 600,
        "Καπλαμάς δρυς": 600,
        "Καπλαμάς καρυδιά": 700
    },
    "Κουζίνα": {
        "Πάγκος/Πλάτη Duropal 60 εκ.": 110,
        "Πάγκος Duropal 90 εκ.": 150,
        "Μελαμίνη πάνω": 350,
        "Μελαμίνη κάτω": 400,
        "Λάκα ματ/σατινέ πάνω": 400,
        "Λάκα ματ/σατινέ κάτω": 450,
        "Λάκα ζαγρέ πάνω": 450,
        "Λάκα ζαγρέ κάτω": 500,
        "Καπλαμάς δρυς πάνω": 450,
        "Καπλαμάς δρυς κάτω": 500
    },
    "Επενδύσεις (απλή)": {
        "Μελαμίνη": 60,
        "Λάκα ματ/σατινέ": 90,
        "Λάκα ζαγρέ": 100,
        "Καπλαμάς δρυς": 100,
        "Καπλαμάς καρυδιά": 150
    },
    "Επενδύσεις (πηχάκια)": {
        "Μελαμίνη": 150,
        "Λάκα ματ/σατινέ": 200,
        "Λάκα ζαγρέ": 250,
        "Καπλαμάς δρυς": 250,
        "Καπλαμάς καρυδιά": 300
    },
    "Επιπλέον Υλικά αναφοράς": {
        "Duropal": 110,
        "Compact": 150,
        "Corian": 600,
        "Εξαρτήματα επίπλων": 300
    }
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
if "furniture_reference_prices" not in st.session_state:
    st.session_state.furniture_reference_prices = def_furniture_reference.copy()
if "furniture_list" not in st.session_state:
    st.session_state.furniture_list = []

# --- Sidebar ---
st.sidebar.markdown("""
    <style>
        .sidebar .sidebar-content {
            background-color: #f3f3f3;
            border-radius: 10px;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

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

    st.subheader("Τιμές Αναφοράς Επίπλων")
    for section, materials in st.session_state.furniture_reference_prices.items():
        with st.expander(section):
            for mat, price in materials.items():
                st.session_state.furniture_reference_prices[section][mat] = st.number_input(
                    f"{mat}",
                    value=float(price),
                    min_value=0.0,
                    key=f"ref_{section}_{mat}"
                )
