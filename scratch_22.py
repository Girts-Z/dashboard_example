import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats

st.title("Pārbaudes darbu rezultātu korelācijas analīze")

st.write("""
Šī lietotne ielādē pārbaudes darbu datus no CSV faila, piemēro vairākus filtrus un ļauj salīdzināt divu izvēlētu pārbaudes darbu tipu rezultātu saistību.
Piemērotie filtri:
- Saglabātas tikai rindas, kur mācību priekšmeta nosaukumā ir iekļauts **Matemātika** vai **Latviešu valoda**.
- Saglabāti tikai tie skolēni, kuriem ir vairāki rezultātu ieraksti (t.i., viens skolēns ir kārtojis vairākus pārbaudes darbus, par kuriem zināms VIIS).
- Attēlotas tikai situācijas, kur abiem izvēlētajiem pārbaudes darbu tipiem ir nenulles rezultāti.
Pēc noklusējuma lietotne salīdzina **Diagnosticējošais darbs** ar **Centralizēts eksāmens** (ar iespēju izvēlēties klases pakāpi katram).
Dati iegūti no VIIS piejamā par skolēnu rezultātiem eksāmenos/diagnosticējošos darbos.
""")

# Augšupielādes sadaļa
uploaded_file = st.file_uploader("Izvēlies CSV failu", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    expected_cols = [
        "Eksāmena kārtošanas personas identifikators",
        "Pārbaudījuma tips",
        "Pārbaudījuma mācību priekšmeta nosaukums",
        "Pārbaudījuma klases pakāpe",
        "Procenti"
    ]
    if not all(col in df.columns for col in expected_cols):
        st.error("Augšupielādētajā CSV failā nav vajadzīgo kolonnu.")
    else:
        # Izņem rindas, kur skolēna ID = 0.
        df = df[df["Eksāmena kārtošanas personas identifikators"].astype(str) != "0"]

        # Mācību priekšmeta izvēle
        # Rādītās opcijas tagad ir "Matemātika" un "Latviešu valoda"
        # Iekšēji filtrējam pēc "Matemātik" un "Latviešu valod"
        subject_dict = {
            "Matemātika": "Matemātik",
            "Latviešu valoda": "Latviešu valod"
        }
        subject_choice = st.sidebar.selectbox("Izvēlies mācību priekšmetu", list(subject_dict.keys()), index=0)
        subject_filter = subject_dict[subject_choice]

        # Filtrējam rindas pēc mācību priekšmeta (case-insensitive)
        df = df[df["Pārbaudījuma mācību priekšmeta nosaukums"].str.contains(subject_filter, case=False, na=False)]

        # Pārliecināmies, ka "Pārbaudījuma klases pakāpe" ir teksts
        df["Pārbaudījuma klases pakāpe"] = df["Pārbaudījuma klases pakāpe"].astype(str)

        # Saglabājam tikai tos skolēnus, kuriem ir vairākas eksāmenu ieraksti.
        student_counts = df["Eksāmena kārtošanas personas identifikators"].value_counts()
        repeated_ids = student_counts[student_counts > 1].index
        df = df[df["Eksāmena kārtošanas personas identifikators"].isin(repeated_ids)]

        st.write(
            f"Ierakstu skaits pēc filtrēšanas ({subject_choice} tikai, ID ≠ 0 un skolēni ar vairākām ierakstiem): {df.shape[0]}")

        # Izvēlies salīdzināmos eksāmenu tipus
        st.sidebar.header("Izvēlies salīdzināmos eksāmenu tipus")
        exam_types = sorted(df["Pārbaudījuma tips"].unique())
        st.sidebar.write("Pieejamie eksāmenu tipi atlasītajos datos:", exam_types)

        default_x = "Diagnosticējošais darbs" if "Diagnosticējošais darbs" in exam_types else exam_types[0]
        default_y = "Centralizēts eksāmens" if "Centralizēts eksāmens" in exam_types else exam_types[0]

        exam_x = st.sidebar.selectbox("Izvēlies eksāmenu tipu X-asi", exam_types, index=exam_types.index(default_x))
        exam_y = st.sidebar.selectbox("Izvēlies eksāmenu tipu Y-asi", exam_types, index=exam_types.index(default_y))


        # Funkcija, lai izvēlētos klases pakāpi atkarībā no eksāmenu tipa.
        def get_grade_filter(exam_type, axis_label):
            df_exam = df[df["Pārbaudījuma tips"] == exam_type]
            available_grades = sorted(df_exam["Pārbaudījuma klases pakāpe"].unique())
            if not available_grades:
                return None
            if exam_type == "Centralizēts eksāmens" and "12" in available_grades:
                default_index = available_grades.index("12")
            else:
                default_index = 0
            return st.sidebar.selectbox(f"Izvēlies klases pakāpi {exam_type} eksāmenam ({axis_label}-asi)",
                                        available_grades, index=default_index)


        grade_filter_x = get_grade_filter(exam_x, "X")
        grade_filter_y = get_grade_filter(exam_y, "Y")

        df_x = df[df["Pārbaudījuma tips"] == exam_x]
        if grade_filter_x:
            df_x = df_x[df_x["Pārbaudījuma klases pakāpe"] == grade_filter_x]

        df_y = df[df["Pārbaudījuma tips"] == exam_y]
        if grade_filter_y:
            df_y = df_y[df_y["Pārbaudījuma klases pakāpe"] == grade_filter_y]

        # Grupējam datus pēc skolēna ID un aprēķinām vidējo rezultātu, ja skolēnam ir vairāki ieraksti
        df_x_grouped = df_x.groupby("Eksāmena kārtošanas personas identifikators")["Procenti"].mean().reset_index()
        df_y_grouped = df_y.groupby("Eksāmena kārtošanas personas identifikators")["Procenti"].mean().reset_index()

        # Apvienojam datus pēc skolēna ID – saglabājam tikai tos, kuriem ir abi eksāmenu tipi.
        merged = pd.merge(df_x_grouped, df_y_grouped,
                          on="Eksāmena kārtošanas personas identifikators",
                          suffixes=("_x", "_y"))

        # Izņemam gadījumus, kur rezultāts ir 0 kādā no eksāmenu tipiem.
        merged = merged[(merged["Procenti_x"] != 0) & (merged["Procenti_y"] != 0)]

        st.write(f"Skolēnu skaits ar abiem eksāmenu tipiem un nenulles rezultātiem: {merged.shape[0]}")

        if merged.shape[0] < 3:
            st.warning("Nepietiekams datu punktu skaits (vajag vismaz 3), lai aprēķinātu nozīmīgu korelāciju.")
        else:
            r, p_value = stats.pearsonr(merged["Procenti_x"], merged["Procenti_y"])
            n = merged.shape[0]
            se = np.sqrt((1 - r ** 2) / (n - 2))

            st.subheader("Korelācijas rezultāti")
            st.write(f"**Pīrsona korelācijas koeficients:** {r:.3f}")
            st.write(f"**Standartkļūda (korelācijas kļūda):** {se:.3f}")
            st.write(f"**P-vērtība:** {p_value:.3f}")

            # Izveidojam grafiku ar galveno izkliedes diagrammu un malu histogrammām.
            fig = plt.figure(figsize=(8, 8))
            gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                                   hspace=0.05, wspace=0.05)
            ax_main = plt.subplot(gs[1, 0])
            ax_xhist = plt.subplot(gs[0, 0], sharex=ax_main)
            ax_yhist = plt.subplot(gs[1, 1], sharey=ax_main)

            # Galvenā izkliedes diagramma ar maziem marķieriem
            ax_main.scatter(merged["Procenti_x"], merged["Procenti_y"], s=10, alpha=0.7)
            ax_main.set_xlabel(f"{exam_x} (Procenti)")
            ax_main.set_ylabel(f"{exam_y} (Procenti)")
            ax_main.set_xlim(0, 100)
            ax_main.set_ylim(0, 100)

            # Aprēķina un uzzīmē reģresijas līniju.
            slope, intercept, r_val, p_val, std_err = stats.linregress(merged["Procenti_x"], merged["Procenti_y"])
            x_vals = np.array([0, 100])
            y_vals = intercept + slope * x_vals
            ax_main.plot(x_vals, y_vals, '--', color='red', label="Regresijas līnija")
            ax_main.legend()

            # Histogramma X-asi
            ax_xhist.hist(merged["Procenti_x"], bins=20, color='gray', alpha=0.7)
            ax_xhist.axis('off')

            # Histogramma Y-asi
            ax_yhist.hist(merged["Procenti_y"], bins=20, orientation='horizontal', color='gray', alpha=0.7)
            ax_yhist.axis('off')

            st.pyplot(fig)
else:
    st.info("Lūdzu, augšupielādē CSV failu, lai sāktu.")
