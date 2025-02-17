import streamlit as st
import pandas as pd
import numpy as np

st.title("School Resource Surplus/Deficit Table")

st.markdown(
    """
For each school and class level (for the selected subject and resource type), the surplus/deficit is computed as:

  Resource Count – Student Count

If any needed data is missing (NaN) for that school/class, the result is marked as unknown and the cell is colored yellow.

**High school mapping:**  
We discard all data for "Padziļinātais kurss". For high‐school, all data from columns whose class level is in **{"Pamatkurss", "10.kl.", "11.kl."}** is combined into a single result column. In the final table, that column is renamed to **"Pamatkurss (10./11.)"**.

Finally, the table is augmented with:
- A new column (“Total”) that sums (column‑wise) the surplus/deficit for each school.
- A new row (“Total”) that sums (row‑wise) the surplus/deficit for each class level.
- In the top‑left corner, the grand total (sum over all schools and class levels) is displayed.

The totals row and column are styled with a light gray background and bold font to set them apart.
"""
)

# -------------------------
# --- Helper: Ensure Unique Labels ---
# -------------------------
def ensure_unique(df):
    # Ensure unique index.
    if not df.index.is_unique:
        counts = {}
        new_index = []
        for item in df.index:
            counts[item] = counts.get(item, 0) + 1
            new_index.append(f"{item}_{counts[item]}" if counts[item] > 1 else item)
        df.index = new_index
    # Ensure unique columns.
    if not df.columns.is_unique:
        counts = {}
        new_cols = []
        for col in df.columns:
            counts[col] = counts.get(col, 0) + 1
            new_cols.append(f"{col}_{counts[col]}" if counts[col] > 1 else col)
        df.columns = new_cols
    return df

# -------------------------
# --- Main Code ---
# -------------------------
# File uploader for CSV or Excel file.
uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Read file based on extension.
    file_extension = uploaded_file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(uploaded_file, header=None)
    elif file_extension in ["xlsx", "xls"]:
        df = pd.read_excel(uploaded_file, header=None)
    else:
        st.error("Unsupported file type")
        st.stop()

    if df.shape[0] < 4:
        st.error("The file does not have the expected structure (at least 4 rows are needed).")
        st.stop()

    # Extract header rows.
    header_row = df.iloc[0].tolist()       # e.g., "4.x", "5.x", "6.x", "11.x"
    class_level_row = df.iloc[1].tolist()    # e.g., "1.kl", "2.kl", etc.
    subject_row = df.iloc[2].tolist()        # Subject info for resource columns
    data_df = df.iloc[3:].reset_index(drop=True)

    # --- Drop columns based on class level and subject ---
    drop_subjects = {"Tiek izmantoti maksas digitālie mācību līdzekļi",
                     "Tiek iegādāti citi mācību materiāli praktisko darbu īstenošanai"}
    indices_to_keep = []
    for i, cl_val in enumerate(class_level_row):
        if i == 0:
            indices_to_keep.append(i)  # always keep school names
        else:
            if str(cl_val).strip() == "Piezīmes":
                continue
            if str(subject_row[i]).strip() in drop_subjects:
                continue
            indices_to_keep.append(i)
    header_row = [header_row[i] for i in indices_to_keep]
    class_level_row = [class_level_row[i] for i in indices_to_keep]
    subject_row = [subject_row[i] for i in indices_to_keep]
    data_df = data_df.iloc[:, indices_to_keep]

    # Reset the DataFrame's columns to sequential integers.
    data_df.columns = range(len(header_row))

    # --- Extract available subjects ---
    subjects = set()
    for i in range(1, len(subject_row)):  # skip first column (school names)
        subj = str(subject_row[i]).strip() if pd.notna(subject_row[i]) else ""
        if subj:
            subjects.add(subj)
    subjects = sorted(list(subjects))
    if not subjects:
        st.error("No subject information found in the file.")
        st.stop()
    selected_subject = st.selectbox("Select Subject", subjects)

    # Let the user choose resource type.
    resource_type = st.radio("Resource Type", options=["Textbooks", "Workbooks"])
    resource_prefix = "5." if resource_type == "Textbooks" else "6."

    # --- Determine class levels for resource data ---
    # (Include columns whose code starts with resource_prefix or "11.", and whose subject matches.)
    class_levels_set = set()
    for i in range(1, len(header_row)):
        code = str(header_row[i]).strip() if pd.notna(header_row[i]) else ""
        cl = str(class_level_row[i]).strip() if pd.notna(class_level_row[i]) else ""
        subj = str(subject_row[i]).strip() if pd.notna(subject_row[i]) else ""
        if (code.startswith(resource_prefix) or code.startswith("11.")) and subj == selected_subject:
            class_levels_set.add(cl)
    # Drop "Padziļinātais kurss" entirely.
    class_levels_set = {cl for cl in class_levels_set if cl != "Padziļinātais kurss"}
    # Combine high-school columns: if any column is one of {"Pamatkurss", "10.kl.", "11.kl."},
    # then use a single result column "Pamatkurss (10./11.)"
    new_class_levels = set()
    if any(cl in {"Pamatkurss", "10.kl.", "11.kl."} for cl in class_levels_set):
        new_class_levels.add("Pamatkurss (10./11.)")
    for cl in class_levels_set:
        if cl not in {"Pamatkurss", "10.kl.", "11.kl."}:
            new_class_levels.add(cl)
    class_levels_list = sorted(list(new_class_levels))
    if not class_levels_list:
        st.error("No class level data found for the selected subject and resource type.")
        st.stop()

    # --- Build DataFrames for surplus/deficit and raw resource counts ---
    schools = data_df.iloc[:, 0]
    result = pd.DataFrame(index=schools, columns=class_levels_list)
    resource_counts = pd.DataFrame(index=schools, columns=class_levels_list)
    for idx, row in data_df.iterrows():
        school = row[0]
        for target in class_levels_list:
            student_unknown = False
            resource_unknown = False
            student_sum = 0
            resource_sum = 0
            student_found = False
            resource_found = False
            for j in range(1, len(header_row)):
                code = str(header_row[j]).strip() if pd.notna(header_row[j]) else ""
                cl_value = str(class_level_row[j]).strip() if pd.notna(class_level_row[j]) else ""
                subj_value = str(subject_row[j]).strip() if pd.notna(subject_row[j]) else ""
                # --- Student counts (columns with code starting with "4.") ---
                if code.startswith("4."):
                    if target == "Pamatkurss (10./11.)" and cl_value in {"Pamatkurss", "10.kl.", "11.kl."}:
                        student_found = True
                        if pd.isna(row[j]):
                            student_unknown = True
                        else:
                            try:
                                student_sum += float(row[j])
                            except:
                                student_unknown = True
                    elif target != "Pamatkurss (10./11.)" and cl_value == target:
                        student_found = True
                        if pd.isna(row[j]):
                            student_unknown = True
                        else:
                            try:
                                student_sum += float(row[j])
                            except:
                                student_unknown = True
                # --- Resource counts (columns with code starting with resource_prefix or "11.") ---
                if (code.startswith(resource_prefix) or code.startswith("11.")) and subj_value == selected_subject:
                    if target == "Pamatkurss (10./11.)" and cl_value in {"Pamatkurss", "10.kl.", "11.kl."}:
                        resource_found = True
                        if pd.isna(row[j]):
                            resource_unknown = True
                        else:
                            try:
                                resource_sum += float(row[j])
                            except:
                                resource_unknown = True
                    elif target != "Pamatkurss (10./11.)" and cl_value == target:
                        resource_found = True
                        if pd.isna(row[j]):
                            resource_unknown = True
                        else:
                            try:
                                resource_sum += float(row[j])
                            except:
                                resource_unknown = True
            if not resource_found or resource_unknown:
                resource_counts.at[school, target] = pd.NA
            else:
                resource_counts.at[school, target] = resource_sum
            if student_unknown or resource_unknown or not student_found or not resource_found:
                result.at[school, target] = pd.NA
            else:
                result.at[school, target] = resource_sum - student_sum

    # --- Discard target columns where every school has 0 or missing resource count ---
    columns_to_drop = []
    for target in result.columns:
        col_vals = resource_counts[target]
        if all(pd.isna(x) or (not pd.isna(x) and float(x) == 0) for x in col_vals):
            columns_to_drop.append(target)
    if columns_to_drop:
        result.drop(columns=columns_to_drop, inplace=True)
        resource_counts.drop(columns=columns_to_drop, inplace=True)

    # Ensure unique labels for the result DataFrame.
    result = ensure_unique(result)
    result = result.astype("float", errors="ignore")
    numeric_result = result.apply(pd.to_numeric, errors="coerce")
    max_abs = numeric_result.abs().max().max()
    if pd.isna(max_abs) or max_abs == 0:
        max_abs = 1

    # --- Add Totals ---
    # Row totals: sum over class levels for each school.
    result["Total"] = result.sum(axis=1, skipna=True)
    # Column totals: sum over schools for each class level (including the "Total" column).
    total_row = result.sum(axis=0, skipna=True)
    total_row.name = "Total"
    # Prepend the totals row (making it the first row).
    result = pd.concat([pd.DataFrame([total_row]), result])

    # --- Define custom styling function ---
    def highlight_totals(df):
        # Create a DataFrame of same shape as df for styles.
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for r in df.index:
            for c in df.columns:
                if r == "Total" or c == "Total":
                    styles.at[r, c] = "background-color: #D3D3D3; font-weight: bold;"
                else:
                    val = df.at[r, c]
                    if pd.isna(val):
                        styles.at[r, c] = "background-color: yellow;"
                    else:
                        try:
                            numeric_val = float(val)
                        except:
                            numeric_val = 0
                        ratio = (abs(numeric_val) / max_abs) ** 0.5
                        intensity = int(255 - ratio * 155)
                        if numeric_val > 0:
                            styles.at[r, c] = f"background-color: rgb({intensity}, 255, {intensity});"
                        elif numeric_val < 0:
                            styles.at[r, c] = f"background-color: rgb(255, {intensity}, {intensity});"
                        else:
                            styles.at[r, c] = ""
        return styles

    def cell_formatter(x):
        if pd.isna(x):
            return "Unknown"
        return f"{int(round(x)):+d}"

    styled_result = result.style.apply(highlight_totals, axis=None).format(cell_formatter)

    st.markdown("### Surplus/Deficit Table with Totals")
    st.markdown(
        f"""
*{resource_type} for the subject **{selected_subject}***.
"""
    )
    st.dataframe(styled_result, use_container_width=True, height=600)
