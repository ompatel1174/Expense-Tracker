import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# === Auto-Refresh Fallback (works in all Streamlit versions)
if "refresh" in st.session_state and st.session_state.refresh:
    st.session_state.refresh = False
    os.execl(sys.executable, sys.executable, *sys.argv)  # full script reload

# === Add New Student UI (with fallback auto-refresh)
st.sidebar.markdown("## ➕ Add New Student Data")

if "refresh" not in st.session_state:
    st.session_state.refresh = False

with st.sidebar.form("new_student_form"):
    name = st.text_input("Student Name")
    age = st.number_input("Age", min_value=1, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    level = st.text_input("Current Educational Level")
    income = st.number_input("Monthly Income", min_value=0, step=500)
    final_expense = st.number_input("Final Monthly Expense", min_value=0, step=500)

    st.markdown("### 📂 Category Expenses")
    food = st.number_input("Food", min_value=0)
    transport = st.number_input("Transport", min_value=0)
    rent = st.number_input("Rent", min_value=0)

    submitted = st.form_submit_button("✅ Add Student")

    if submitted:
        new_row = {
            'Name': name,
            #'Age': age,
            #'Gender': gender,
            #'Current educational level': level,
            'Monthly Income': income,
            'Final Monthly Expense': final_expense,
            'Food': food,
            'Transport': transport,
            'Rent': rent
        }

        file_path = "student_monthly_expences.xlsx"

        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_excel(file_path, index=False)
        st.success(f"✅ Student '{name}' added successfully!")
        st.session_state.refresh = True


# === Load Monthly Data
@st.cache_data
def load_monthly_data():
    df = pd.read_excel("student_monthly_expences.xlsx")
    exclude_cols = ['Name', 'Age', 'Gender', 'Current educational level', 'Monthly Income', 'Final Monthly Expense']
    category_cols = [col for col in df.columns if col not in exclude_cols]

    long_df = df[['Name', 'Monthly Income'] + category_cols].melt(
        id_vars=['Name', 'Monthly Income'],
        var_name='category',
        value_name='amount'
    )
    long_df['date'] = pd.to_datetime("2025-07-01") 
    return long_df

# === Load Daily Data
@st.cache_data
def load_daily_data():
    df = pd.read_excel("daily_expense_data_1.xlsx")
    df.columns = df.columns.str.strip().str.lower()
    df['date'] = pd.to_datetime(df['date'])
    df['Name'] = 'You'
    return df

# === Load Data
monthly_df = load_monthly_data()
daily_df = load_daily_data()

st.set_page_config(layout="wide")
st.title("📊 Interactive Expense Tracker Dashboard")

view_option = st.sidebar.radio("Choose Data View", ["Monthly (by Student)", "Daily"])

# === Monthly View
if view_option == "Monthly (by Student)":
    source_df = monthly_df.copy()
    student_names = source_df['Name'].unique()
    selected_student = st.sidebar.selectbox("Select a student", student_names)
    source_df = source_df[source_df['Name'] == selected_student]
    monthly_income = source_df['Monthly Income'].iloc[0]

    all_categories = ['All'] + sorted(source_df['category'].unique())
    selected_category = st.sidebar.selectbox("Filter by Category", all_categories)

    if selected_category != 'All':
        filtered_df = source_df[source_df['category'] == selected_category]
    else:
        filtered_df = source_df

    total_spent = source_df['amount'].sum()
    filtered_spent = filtered_df['amount'].sum()
    remaining = monthly_income - total_spent
    top_category = source_df.groupby('category')['amount'].sum().idxmax()

    st.markdown(" 💰 Expense Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly Income", f"₹{monthly_income:,.0f}")
    col2.metric("Total Spent", f"₹{total_spent:,.0f}")
    col3.metric("Remaining", f"₹{remaining:,.0f}", delta_color="inverse")
    col4.metric("Top Spending", top_category)

    st.markdown("### 📊 Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        bar_fig = px.bar(filtered_df, x='category', y='amount', color='amount', title='Spending by Category', color_continuous_scale='blues')
        st.plotly_chart(bar_fig, use_container_width=True)
    with col2:
        pie_fig = px.pie(filtered_df, names='category', values='amount', hole=0.4, title='Category-wise Distribution')
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("### 📅 Overall Daily Expense Trend by Student")
    trend_df = daily_df.groupby(['date', 'Name'])['amount'].sum().reset_index()
    line_fig = px.line(trend_df, x='date', y='amount', color='Name', title='📅 Daily Spending Comparison by Student', markers=True)
    st.plotly_chart(line_fig, use_container_width=True)

    if not filtered_df.empty:
        st.markdown("### 📌 Category Expense Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Expense", f"₹{total_spent:,.0f}")
        col2.metric("Selected Category Expense", f"₹{filtered_spent:,.0f}")
        if selected_category != 'All':
            percent = (filtered_spent / total_spent) * 100
            col3.metric("Category % of Total", f"{percent:.2f}%")

# === Daily View
else:
    source_df = daily_df.copy()
    selected_student = 'You'
    available_dates = sorted(source_df['date'].dt.date.unique())
    selected_date = st.sidebar.date_input("Select a date", min_value=min(available_dates), max_value=max(available_dates))
    filtered_df = source_df[source_df['date'].dt.date == selected_date]
    daily_total = filtered_df['amount'].sum()
    st.subheader(f"🗓️ Date: {selected_date.strftime('%d %B %Y')} | 💸 Net Amount Spent: ₹{daily_total:,.0f}")

    st.markdown("### 📊 Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        if not filtered_df.empty:
            bar_fig = px.bar(filtered_df, x='category', y='amount', color='amount', title='Spending by Category', color_continuous_scale='blues')
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No data to display for the selected date.")
    with col2:
        if not filtered_df.empty:
            pie_fig = px.pie(filtered_df, names='category', values='amount', hole=0.4, title='Category-wise Distribution')
            st.plotly_chart(pie_fig, use_container_width=True)
