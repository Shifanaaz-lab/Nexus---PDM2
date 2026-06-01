import streamlit as st
import time

if "count" not in st.session_state:
    st.session_state.count = 0

def main():
    st.write("Main run count:", st.session_state.count)
    st.session_state.count += 1
    
    @st.fragment(run_every=2)
    def my_frag():
        st.write("Fragment timestamp:", time.time())
        
    my_frag()

if __name__ == "__main__":
    main()
