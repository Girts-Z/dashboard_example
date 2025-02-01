# app.py
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(layout="wide", page_title="Skolu datu panelis")

# ---------------------------------------
# Ielādējam datus no Excel faila
# ---------------------------------------
excel_file = r"school_dashboard_data2.xlsx"
xl = pd.ExcelFile(excel_file)

schools_df = xl.parse("Schools")
exam_perf_df = xl.parse("ExamPerformance")
country_avg_df = xl.parse("CountryAverage")
satisfaction_df = xl.parse("Satisfaction")
proficiency_df = xl.parse("ProficiencyDistribution")
extra_curriculars_df = xl.parse("ExtraCurriculars")
student_numbers_df = xl.parse("StudentNumbers")

# ---------------------------------------
# Iegūstam izvēlētās skolas datus
# ---------------------------------------
st.sidebar.header("Izvēlies skolu")
school_selected = st.sidebar.selectbox("Skola", schools_df["School"].unique())
school_info = schools_df[schools_df["School"] == school_selected].iloc[0]
map_data = pd.DataFrame({
    "lat": [school_info["Latitude"]],
    "lon": [school_info["Longitude"]]
})

# ============================================================================
# TOP RĀDĀJS: Augšējā rinda – divi tilei: (1) Skolas informācija un (2) Kopējais skolēnu skaits
# ============================================================================
top_cols = st.columns(2)

with top_cols[0]:
    st.subheader("Skolas informācija")
    st.title(school_selected)
    st.markdown(f"**Adrese:** {school_info['Address']}")
    st.markdown(f"**Direktors:** {school_info['Director']}")
    st.markdown(f"**E-pasts:** {school_info['Email']}")
    st.map(map_data)

with top_cols[1]:
    # Instead of placing the header outside the container,
    # we now include it in an HTML container with no extra margin.
    st.markdown(
        """
        <div style="height:350px; display:flex; flex-direction:column; justify-content:flex-end; margin:0; padding:0;">
            <h3 style="margin:0; padding:0;">Kopējais skolēnu skaits pēdējos piecos gados</h3>
        """, unsafe_allow_html=True)
    student_data = student_numbers_df[student_numbers_df["School"] == school_selected]
    chart_students = alt.Chart(student_data).mark_line(point=True).encode(
        x=alt.X("Year:O", title="Gads"),
        y=alt.Y("StudentCount:Q", title="Skolēnu skaits"),
        tooltip=["Year", "StudentCount"]
    ).properties(width=600, height=300)
    st.altair_chart(chart_students, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# RINDA 2: Divi tilei – (1) Eksāmenu rezultāti un (2) Skolēnu apmierinātība
# ============================================================================
row2_cols = st.columns(2)

with row2_cols[0]:
    st.subheader("Eksāmenu rezultāti")
    # Eksāmu atlase: šī izvēle ietekmē tikai šo tile
    school_exam_data = exam_perf_df[exam_perf_df["School"] == school_selected]
    exam_selected = st.selectbox("Izvēlies eksāmenu", school_exam_data["Exam"].unique(), key="exam_selection")
    exam_data = school_exam_data[school_exam_data["Exam"] == exam_selected].copy()
    # Savieno datus ar valsts vidējo rādītāju (katram gadam)
    exam_data = exam_data.merge(
        country_avg_df[country_avg_df["Exam"] == exam_selected],
        on="Year",
        how="left"
    )
    # Sagatavo datus: gan skolas rezultāts ("Skolas rezultāts") un valsts vidējais ("Valsts vidējais")
    df_plot = exam_data.melt(
        id_vars=["Year", "Kārtotāju skaits"],
        value_vars=["Skolas rezultāts", "Valsts vidējais"],
        var_name="Tips",
        value_name="Rezultāts"
    )
    chart_exam = alt.Chart(df_plot).mark_bar().encode(
        x=alt.X("Year:O", title="Gads"),
        xOffset=alt.X("Tips:N", title="Rādītājs"),
        y=alt.Y("Rezultāts:Q", title="Eksāmena rezultāts"),
        color=alt.Color("Tips:N", title="Rādītājs", scale=alt.Scale(range=["steelblue", "orange"])),
        tooltip=["Year", "Tips", "Rezultāts", "Kārtotāju skaits"]
    ).properties(width=600, height=400)
    text = alt.Chart(df_plot[df_plot["Tips"] == "Skolas rezultāts"]).mark_text(
        dy=-5,
        color="white"
    ).encode(
        x=alt.X("Year:O"),
        xOffset=alt.X("Tips:N"),
        y=alt.Y("Rezultāts:Q"),
        text=alt.Text("Kārtotāju skaits:Q")
    )
    final_exam_chart = chart_exam + text
    st.altair_chart(final_exam_chart, use_container_width=True)

with row2_cols[1]:
    st.subheader("Skolēnu apmierinātība")
    satisfaction_filter = st.radio("Izvēlies līmeni",
                                   ["Visi", "I prasmju līmenis", "II prasmju līmenis", "III prasmju līmenis", "IV prasmju līmenis"],
                                   key="satisfaction_filter")
    satisfaction_data = satisfaction_df[
        (satisfaction_df["School"] == school_selected) &
        (satisfaction_df["Proficiency"] == satisfaction_filter)
    ]
    if not satisfaction_data.empty:
        chart_sat = alt.Chart(satisfaction_data).mark_line(point=True).encode(
            x=alt.X("Year:O", title="Gads"),
            y=alt.Y("Satisfaction:Q", title="Apmierinātība (%)"),
            tooltip=["Year", "Satisfaction"]
        ).properties(width=600, height=300)
        st.altair_chart(chart_sat, use_container_width=True)
    else:
        st.write("Nav datu attiecīgajam filtram.")

st.markdown("---")

# ============================================================================
# RINDA 3: Divi tilei – (1) Prasmju sadalījums un (2) Interešu izglītība
# ============================================================================
row3_cols = st.columns(2)

with row3_cols[0]:
    st.subheader("Prasmju sadalījums (procentos)")
    proficiency_data = proficiency_df[proficiency_df["School"] == school_selected]
    chart_proficiency = alt.Chart(proficiency_data).mark_bar().encode(
        y=alt.Y("Year:O", title="Gads"),
        x=alt.X("sum(Percentage):Q", stack="normalize", title="Procentu sadalījums"),
        color=alt.Color("Proficiency:N", title="Prasmju līmenis",
                        sort=["I prasmju līmenis", "II prasmju līmenis", "III prasmju līmenis", "IV prasmju līmenis"]),
        tooltip=[alt.Tooltip("Proficiency:N", title="Prasmju līmenis"),
                 alt.Tooltip("Percentage:Q", title="Procenti")]
    ).properties(width=600, height=300)
    st.altair_chart(chart_proficiency, use_container_width=True)

with row3_cols[1]:
    st.subheader("Interešu izglītība")
    ec_data = extra_curriculars_df[extra_curriculars_df["School"] == school_selected]
    ec_grouped = ec_data.groupby("Category").agg(Count=("ExtraCurricular", "count")).reset_index()
    ec_list = ec_data.groupby("Category")["ExtraCurricular"].apply(lambda x: ", ".join(x)).reset_index().rename(columns={"ExtraCurricular": "Aktivitātes"})
    ec_grouped = ec_grouped.merge(ec_list, on="Category", how="left")
    fig = px.pie(ec_grouped, names='Category', values='Count', title='Interešu izglītība pēc kategorijām')
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Skaits: %{value}<br>Aktivitātes: %{customdata}<extra></extra>',
        customdata=ec_grouped["Aktivitātes"]
    )
    # Disable legend interactivity (clicking will not remove a category)
    fig.update_layout(legend=dict(itemclick=False, itemdoubleclick=False))
    st.plotly_chart(fig, use_container_width=True)

