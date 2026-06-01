import streamlit as st
import time

refresh_secs = st.sidebar.slider("Interval", 0, 10, 0)

def render(label):
    st.write(f"Current time: {time.time()} - {label}")
    st.slider("Top N", 1, 10, 5, key=f"top_n_{label}")

if refresh_secs > 0:
    @st.fragment(run_every=int(refresh_secs))
    def dash():
        render("A")
    dash()
else:
    render("B")
