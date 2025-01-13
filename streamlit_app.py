import streamlit as st

st.title("Analiza Podataka")

with open("main.py", "r") as file:
    exec(file.read())