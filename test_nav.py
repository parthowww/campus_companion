import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.write("Login")

def dashboard():
    st.write("Dashboard")

if st.session_state.logged_in:
    pg = st.navigation([st.Page(dashboard, title="Dashboard")])
else:
    pg = st.navigation([st.Page(login, title="Login")])
pg.run()
