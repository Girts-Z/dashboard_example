import streamlit as st
import pandas as pd
import altair as alt

st.title("Pašvaldību pašvērtējumu apkopojums")

# Create the DataFrame from your data
data = {
    "Pašvaldība": [
        "Aizkraukles_novads", "Alūksnes novads", "Augšdaugavas novads", "Balvu novads", "Cēsu novads",
        "Dienvidkurzemes novads", "Dobeles_ novads", "Gulbenes novads", "Jelgava", "Jelgavas novads",
        "Jēkabpils novada pašvaldība", "Jūrmala", "Krāslavas novads", "Kuldīgas novads",
        "Ķekavas novada pašvaldība", "Liepajas_valstspilseta", "Limbažu novads", "Līvānu_novads",
        "Ludzas novads", "Madonas novads", "Marupes novads", "Ogres_novads", "Olaines novada pašvaldība",
        "Rēzekne", "Rēzeknes novads", "Ropazu_novads", "Saldus novads", "Siguldas novads",
        "Smiltenes novads", "TalsuNovads_", "Tukuma novads", "VALMIERAS-NOVADS_", "Valkas novads",
        "Ventspils novads", "Ādažu novads", "Preilu_novads", "Bauskas novads", "Ventspils"
    ],
    "DARBA AR JAUNATNI KVALITATĪVAS UN ILGTSPĒJĪGAS SISTĒMAS IZVEIDE UN ATTĪSTĪBA": [
        39, 32, 34, 38, 34, 28, 44, 37, 40, 44, 28, 43, 23, 35, 16, 43, 9, 29, 23, 46,
        22, 28, 25, 35, 25, 32, 39, 31, 25, 41, 32, 34, 20, 28, 20, 32, 47, 33
    ],
    "DARBĀ AR JAUNATNI IESAISTĪTAIS PERSONĀLS": [
        19, 20, 29, 30, 28, 14, 28, 29, 29, 32, 24, 29, 18, 25, 14, 26, 19, 22, 21, 37,
        19, 19, 28, 23, 28, 25, 27, 18, 17, 29, 23, 30, 15, 7, 14, 23, 30, 20
    ],
    "JAUNIEŠU LĪDZDALĪBAS VEICINĀŠANA": [
        51, 46, 50, 63, 67, 36, 62, 61, 47, 65, 66, 66, 42, 62, 21, 62, 50, 61, 52, 62,
        53, 55, 56, 60, 53, 55, 66, 38, 39, 61, 43, 55, 52, 39, 18, 60, 74, 41
    ],
    "DARBA AR JAUNATNI ĪSTENOŠANA": [
        71, 76, 81, 83, 79, 42, 80, 84, 71, 73, 83, 73, 58, 66, 59, 68, 69, 67, 73, 83,
        60, 63, 72, 67, 66, 82, 82, 42, 44, 69, 49, 77, 63, 44, 37, 73, 90, 72
    ]
}

df = pd.DataFrame(data)

# Compute the total score ("Kopā")
df['Kopā'] = (
    df["DARBA AR JAUNATNI KVALITATĪVAS UN ILGTSPĒJĪGAS SISTĒMAS IZVEIDE UN ATTĪSTĪBA"] +
    df["DARBĀ AR JAUNATNI IESAISTĪTAIS PERSONĀLS"] +
    df["JAUNIEŠU LĪDZDALĪBAS VEICINĀŠANA"] +
    df["DARBA AR JAUNATNI ĪSTENOŠANA"]
)

# Define the selection options for the criteria (including total "Kopā")
criteria_options = [
    "DARBA AR JAUNATNI KVALITATĪVAS UN ILGTSPĒJĪGAS SISTĒMAS IZVEIDE UN ATTĪSTĪBA",
    "DARBĀ AR JAUNATNI IESAISTĪTAIS PERSONĀLS",
    "JAUNIEŠU LĪDZDALĪBAS VEICINĀŠANA",
    "DARBA AR JAUNATNI ĪSTENOŠANA",
    "Kopā"
]

# Define maximum y-axis values for each criterion (adjust these as needed)
y_max_values = {
    "DARBA AR JAUNATNI KVALITATĪVAS UN ILGTSPĒJĪGAS SISTĒMAS IZVEIDE UN ATTĪSTĪBA": 52,
    "DARBĀ AR JAUNATNI IESAISTĪTAIS PERSONĀLS": 40,
    "JAUNIEŠU LĪDZDALĪBAS VEICINĀŠANA": 78,
    "DARBA AR JAUNATNI ĪSTENOŠANA": 100,
    "Kopā": 52+40+78+100
}

# Let the user select a criterion from the sidebar
selected_criterion = st.sidebar.selectbox("Izvēlies kritēriju:", criteria_options)

# Sort the data in descending order based on the selected criterion
df_sorted = df.sort_values(by=selected_criterion, ascending=False)

# Compute the average for the selected criterion
avg_value = df[selected_criterion].mean()
st.write(f"Zemāk uzzīmēta stabiņu diagramma izvēlētajam kritērijam, kas saranžē pašvaldības pēc kopsummas. Ar sarkanu raustītu līniju attēlots vidējais rezultāts, vertikālā ass iet līdz maksimāli iespējamajam rezultātam.")
st.write(f"Vidējais rezultāts šajā kritērijā: {avg_value:.2f}")

# Create an Altair bar chart for the selected criterion with fixed width.
bars = alt.Chart(df_sorted).mark_bar().encode(
    x=alt.X('Pašvaldība:N',
            sort=None,
            axis=alt.Axis(
                labelAngle=-45,
                labelOverlap=False,
                labelFontSize=10,   # smaller font to help fit more labels
                title="Pašvaldība"
            )),
    y=alt.Y(f'{selected_criterion}:Q',
            scale=alt.Scale(domain=[0, y_max_values[selected_criterion]]),
            title="Rezultāts"),
    tooltip=['Pašvaldība', f'{selected_criterion}:Q']
).properties(
    title=f"Pašvaldības sakārtotas pēc: {selected_criterion}",
    width=800,
    height=400
)

# Create a horizontal rule to mark the average value
avg_line = alt.Chart(pd.DataFrame({'avg': [avg_value]})).mark_rule(
    color='red',
    strokeDash=[5, 5]
).encode(
    y='avg:Q'
)

# Overlay the average line on the bar chart
chart = bars + avg_line

st.altair_chart(chart, use_container_width=False)
