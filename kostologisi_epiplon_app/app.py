import streamlit as st
import fitz  # PyMuPDF
import ezdxf
import tempfile
import os

# --- Τιμές Υλικών ανά m² ---
material_prices = {
    "Καπλαμάς Δρυς": 160,
    "Λάκα": 120,
    "Μελαμίνη": 80
}

def extract_pdf_dimensions(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        # Αναζήτηση για αριθμούς τύπου "2.5m2" ή "1500 x 600"
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

st.header("2. Εισαγωγή Διαστάσεων Επιφανειών (σε m²)")
def_area_help = "Αν έχει ανέβει αρχείο, προτείνεται αυτόματα. Μπορείς να το τροποποιήσεις."
exterior_area = st.number_input("Εξωτερική επιφάνεια (πόρτες, ράφια, σώμα, πλάτη)", min_value=0.0, step=0.1, value=auto_area, help=def_area_help)
interior_area = st.number_input("Εσωτερική επιφάνεια (ράφια, σώμα, πλάτη)", min_value=0.0, step=0.1, help=def_area_help)

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
    st.write(f"✅ Κόστος εξωτερικών υλικών: {exterior_cost:.2f} €")
    st.write(f"✅ Κόστος εσωτερικών υλικών: {interior_cost:.2f} €")
    st.write(f"✅ Κόστος συρταριών ({drawer_count} × 250€): {drawers_cost:.2f} €")
    st.markdown("---")
    st.success(f"💰 Συνολικό Κόστος Κατασκευής: {total_cost:.2f} €")
