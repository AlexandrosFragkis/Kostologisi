try:
    import streamlit as st
except ModuleNotFoundError:
    raise ImportError("Το Streamlit δεν είναι εγκατεστημένο. Εκτέλεσε 'pip install streamlit' για να συνεχίσεις.")

import fitz  # PyMuPDF
import ezdxf
import tempfile
import os

st.set_page_config(layout="wide")

# --- Προεπιλεγμένες Τιμές Υλικών για Κοστολόγηση ---
def_material_prices = {
    "Καπλαμάς": 130,
    "Λάκα": 95,
    "Μελαμίνη": 60
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
    "Μελαμίνη": 60
}

# Εισαγωγή Τιμών Υλικών για Κοστολόγηση
st.sidebar.header("Τιμές Υλικών Κοστολόγησης (€ / m²)")
material_prices = {}
for mat in def_material_prices:
    material_prices[mat] = st.sidebar.number_input(f"{mat}", value=float(def_material_prices[mat]), min_value=0.0)

# Επεξεργάσιμη Λίστα Τιμών Αναφοράς
st.sidebar.header("Τιμές Αναφοράς Υλικών")
material_reference_prices = {}
for mat in def_material_reference:
    material_reference_prices[mat] = st.sidebar.number_input(f"{mat} ", value=float(def_material_reference[mat]), min_value=0.0, key=f"ref_{mat}")

# --- Functions ---
def extract_pdf_dimensions(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        import re
        areas = re.findall(r"(\d+\.?\d*)\s*(?:m2|m²)", text)
        if areas:
            total_area = sum([float(a) for a in areas])
            return total_area
        return 0.0
    except Exception as e:
        st.error(f"Σφάλμα κατά την ανάγνωση PDF: {e}")
        return 0.0

def extract_dxf_dimensions(file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()

        total_area = 0.0
        for entity in msp:
            if entity.dxftype() == 'LWPOLYLINE' and entity.closed:
                total_area += abs(entity.area) / 1_000_000  # mm² -> m²

        os.remove(tmp_path)
        return round(total_area, 2)
    except Exception as e:
        st.error(f"Σφάλμα κατά την ανάγνωση DXF: {e}")
        return 0.0

# --- Εφαρμογή ---
st.title("📐 Κοστολόγηση Custom Επίπλων")

st.header("1. Ανέβασμα Αρχείων Σχεδίου (PDF ή CAD)")
uploaded_file = st.file_uploader("Ανέβασε αρχείο PDF ή DXF", type=["pdf", "dxf"])

auto_area = 0.0
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext == "pdf":
        auto_area = extract_pdf_dimensions(uploaded_file)
    elif file_ext == "dxf":
        auto_area = extract_dxf_dimensions(uploaded_file)

    st.info(f"🔍 Εντοπίστηκε συνολική επιφάνεια από το σχέδιο: {auto_area:.2f} m²")

st.header("2. Εισαγωγή Διαστάσεων Κατασκευής (σε εκατοστά)")
def_area_help = "Αν έχει ανέβει αρχείο, προτείνεται αυτόματα. Μπορείς να το τροποποιήσεις."
exterior_length = st.number_input("Μήκος εξωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0, help=def_area_help)
exterior_height = st.number_input("Ύψος εξωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0, help=def_area_help)
interior_length = st.number_input("Μήκος εσωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0, help=def_area_help)
interior_height = st.number_input("Ύψος εσωτερικής επιφάνειας (cm)", min_value=0.0, step=1.0, help=def_area_help)

# Υπολογισμός επιφανειών σε m²
exterior_area = round((exterior_length * exterior_height) / 10000, 2)
interior_area = round((interior_length * interior_height) / 10000, 2)

st.header("3. Επιλογή Υλικών")
exterior_material = st.selectbox("Υλικό εξωτερικά", options=list(material_prices.keys()))
interior_material = st.selectbox("Υλικό εσωτερικά", options=list(material_prices.keys()))

st.header("4. Συρτάρια")
drawer_count = st.number_input("Αριθμός συρταριών", min_value=0, step=1)
drawer_price = 250

if st.button("Υπολογισμός Κόστους"):
    exterior_cost = exterior_area * material_prices[exterior_material]
    interior_cost = interior_area * material_prices[interior_material]
    drawers_cost = drawer_count * drawer_price
    total_cost = exterior_cost + interior_cost + drawers_cost

    st.subheader("Ανάλυση Κόστους")
    st.write(f"✅ Κόστος εξωτερικών υλικών: {exterior_cost:.2f} € (επιφάνεια: {exterior_area} m²)")
    st.write(f"✅ Κόστος εσωτερικών υλικών: {interior_cost:.2f} € (επιφάνεια: {interior_area} m²)")
    st.write(f"✅ Κόστος συρταριών ({drawer_count} × 250€): {drawers_cost:.2f} €")
    st.markdown("---")
    st.success(f"💰 Συνολικό Κόστος Κατασκευής: {total_cost:.2f} €")

    st.header("5. Επιπλέον Υπολογισμοί")
    manual_cost = st.number_input("Χειροκίνητο συνολικό κόστος κατασκευής (€)", min_value=0.0, max_value=1000000.0, step=100.0)
    commission_percent = st.number_input("Ποσοστό προμήθειας αρχιτέκτονα (%)", min_value=0.0, max_value=100.0, step=1.0)
    commission_amount = manual_cost * (commission_percent / 100)
    final_cost = manual_cost + commission_amount
    st.write(f"🔧 Προμήθεια ({commission_percent:.0f}%): {commission_amount:.2f} €")
    st.success(f"🏁 Τελικό Κόστος με Προμήθεια: {final_cost:.2f} €")
