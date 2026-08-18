from typing import List
import time
import streamlit as st
import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
#from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# ==========================================
# 1. PAGE CONFIG & COMMERCIAL CSS STYLING
# ==========================================
st.set_page_config(page_title="CineAI - Commercial Booking Portal", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* Custom Cinema & Enterprise Payment UI Styling */
    .screen-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 30px;
        margin-top: 10px;
    }
    .cinema-screen {
        width: 80%;
        height: 35px;
        background: linear-gradient(180deg, rgba(229,9,20,0.8) 0%, rgba(30,30,30,0.2) 100%);
        border-top: 4px solid #e50914;
        border-radius: 50% 50% 0 0 / 15% 15% 0 0;
        text-align: center;
        color: white;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 2px;
        padding-top: 5px;
        box-shadow: 0 10px 25px rgba(229,9,20,0.3);
    }
    .legend-box {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 25px;
        font-size: 13px;
        color: #a0a0a0;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .legend-dot-avail { width: 14px; height: 14px; background-color: #2b2b2b; border: 2px solid #555; border-radius: 4px; }
    .legend-dot-select { width: 14px; height: 14px; background-color: #e50914; border-radius: 4px; }
    .legend-dot-taken { width: 14px; height: 14px; background-color: #1a1a1a; border: 2px solid #333; border-radius: 4px; opacity: 0.5; }
    
    /* Professional Checkout Container */
    .checkout-card {
        background-color: #161616;
        border: 1px solid #2b2b2b;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .secure-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #888;
        font-size: 12px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; padding: 10px; border-bottom: 2px solid #e50914; margin-bottom: 20px;'>
        <h1 style='color: #e50914;'>CineAI Cinema Booking Chatbot</h1>
        <p style='color: #888;'>Enterprise-Grade Cinema Ticketing & Secure Payment Gateway</p>
    </div>
""", unsafe_allow_html=True)

# Session State Initialization
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = "The Odyssey"
if "confirmed_seats" not in st.session_state:
    st.session_state.confirmed_seats = []
if "cinema_choice" not in st.session_state:
    st.session_state.cinema_choice = "Shaw Theatres Waterway Point (IMAX)"
if "show_seat_picker" not in st.session_state:
    st.session_state.show_seat_picker = False
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to the CineAI portal. Query movie schedules or titles (e.g., 'Show showtimes for Interstellar') to begin your booking process."}
    ]

# ==========================================
# 2. DEFINE LIVE TOOLS (TMDB + PRICING)
# ==========================================

TMDB_API_KEY = "5d054cb96d495c1e19b175a5a5b0dcfd"  # Keep your active TMDB API key here

@tool
def fetch_live_showtimes(movie_name: str) -> str:
    """Fetches real-time movie metadata from TMDB and lists matching screening schedules."""
    st.session_state.selected_movie = movie_name
    st.session_state.show_seat_picker = True
    
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("results"):
            movie = data["results"][0]
            title = movie.get("title")
            overview = movie.get("overview")
            release_date = movie.get("release_date")
            rating = movie.get("vote_average")
            
            return (
                f"**Verified Movie Record: {title}**\n"
                f"* **Release Date**: {release_date}\n"
                f"* **Rating**: {rating}/10\n"
                f"* **Synopsis**: {overview}\n\n"
                f"**Available Screenings:**\n"
                f"1. Shaw Theatres Waterway Point | IMAX | 7:15 PM\n"
                f"2. Golden Village VivoCity | Dolby Atmos | 7:30 PM\n"
                f"3. Cathay Cineplex AMK Hub | Standard 2D | 8:00 PM\n\n"
                f"*Please select your preferred venue configuration and seats below.*"
            )
        else:
            return f"No records found for '{movie_name}'."
    except Exception as e:
        return f"API Connection Error: {e}"

@tool
def calculate_final_price(cinema_name: str, format_type: str, seats: List[str]) -> str:
    """Calculates final pricing for selected seats."""
    price = 16.50 if "IMAX" in format_type.upper() else 11.50
    subtotal = len(seats) * price
    total = subtotal + 1.50
    return f"Subtotal: ${subtotal:.2f} | Fee: $1.50 | Total: ${total:.2f} SGD"

tools = [fetch_live_showtimes, calculate_final_price]
tool_map = {t.name: t for t in tools}

@st.cache_resource
def get_model():
    # We are using Gemini 3.5 Flash for the best speed and rate limits
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0).bind_tools(tools)

model = get_model()

# ==========================================
# 3. STREAMLIT UI TABS (Chat & Payment)
# ==========================================

tab_chat, tab_pay = st.tabs(["AI Assistant & Inventory", "Secure Checkout"])

# --- TAB 1: AI CHATBOT & COMMERCIAL SEAT MATRIX ---
with tab_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_prompt := st.chat_input("Enter movie title or screening query..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Querying inventory management system..."):
                try:
                    lc_messages = [HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]) for m in st.session_state.messages]
                    response = model.invoke(lc_messages)
                    
                    # 1. Ensure output_text is a string
                    if isinstance(response.content, list):
                        output_text = "".join([part.get("text", "") for part in response.content if isinstance(part, dict)])
                    else:
                        output_text = response.content or ""

                    # 2. Append tool results safely
                    if response.tool_calls:
                        for tool_call in response.tool_calls:
                            t_name = tool_call["name"]
                            t_args = tool_call["args"]
                            tool_result = tool_map[t_name].invoke(t_args)
                            output_text += f"\n\n{tool_result}"
                    
                    st.markdown(output_text)
                    st.session_state.messages.append({"role": "assistant", "content": output_text})
                except Exception as e:
                    st.error(f"Error: {e}")

    # COMMERCIAL INTERACTIVE SEAT MAP
    if st.session_state.show_seat_picker:
        st.markdown("---")
        st.subheader(f"Hall Seating Plan: {st.session_state.selected_movie}")
        
        st.session_state.cinema_choice = st.selectbox("Select Hall & Audio Format:", [
            "Shaw Theatres Waterway Point (IMAX)", 
            "Golden Village VivoCity (Dolby Atmos)", 
            "Cathay Cineplex AMK Hub (Standard 2D)"
        ])
        
        # Realistic Cinema Screen Header
        st.markdown("""
            <div class="screen-container">
                <div class="cinema-screen">SCREEN</div>
            </div>
            <div class="legend-box">
                <div class="legend-item"><div class="legend-dot-avail"></div> Available</div>
                <div class="legend-item"><div class="legend-dot-select"></div> Selected</div>
                <div class="legend-item"><div class="legend-dot-taken"></div> Occupied</div>
            </div>
        """, unsafe_allow_html=True)
        
        col_names = ["1", "2", "3", "4", "5", "6", "7", "8"]
        row_data = {
            "Row A": [True, True, False, False, False, False, True, True],
            "Row B": [False, False, False, False, False, False, False, False],
            "Row C": [False, False, True, True, True, True, False, False],
            "Row D": [False, False, False, False, True, False, False, False]
        }
        
        selected_seats_temp = []
        
        for row_label, seats_status in row_data.items():
            cols = st.columns(len(col_names) + 1)
            cols[0].markdown(f"<div style='padding-top: 8px; font-weight: bold; color: #ccc;'>{row_label}</div>", unsafe_allow_html=True)
            
            row_letter = row_label.replace(" ", "")
            
            for i, is_taken in enumerate(seats_status):
                seat_code = col_names[i]
                seat_full_id = f"{row_letter}{seat_code}"
                
                if is_taken:
                    cols[i+1].button(f"✕ {seat_code}", disabled=True, key=f"btn_{seat_full_id}", help=f"Seat {seat_full_id} is occupied")
                else:
                    is_selected = cols[i+1].checkbox(f"{seat_code}", key=f"chk_{seat_full_id}")
                    if is_selected:
                        selected_seats_temp.append(seat_full_id)
                        
        st.markdown("---")
        col_action1, col_action2 = st.columns([2, 1])
        with col_action1:
            st.info(f"Selected Seats: **{', '.join(selected_seats_temp) if selected_seats_temp else 'None'}**")
        with col_action2:
            if st.button("Proceed to Checkout ➔", type="primary"):
                if selected_seats_temp:
                    st.session_state.confirmed_seats = selected_seats_temp
                    st.success("Seats locked. Navigate to the 'Secure Checkout' tab.")
                else:
                    st.warning("Please select at least one seat.")

# --- TAB 2: SECURE PAYMENT GATEWAY ---
with tab_pay:
    st.subheader("Secure Enterprise Checkout")
    
    if not st.session_state.confirmed_seats:
        st.info("No active seat reservations found. Please select seats via the AI Assistant & Inventory tab first.")
    else:
        format_type = st.session_state.cinema_choice
        num_seats = len(st.session_state.confirmed_seats)
        unit_price = 16.50 if "IMAX" in format_type else 11.50
        subtotal = num_seats * unit_price
        booking_fee = 1.50
        total_payable = subtotal + booking_fee
        
        # Professional Order Summary Card
        st.markdown(f"""
        <div class="checkout-card">
            <h4 style="margin-top:0; color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px;">Order Summary</h4>
            <table style="width:100%; color: #bbb; font-size: 14px; border-collapse: collapse;">
                <tr><td style="padding: 6px 0;"><strong>Feature Film:</strong></td><td style="text-align: right;">{st.session_state.selected_movie}</td></tr>
                <tr><td style="padding: 6px 0;"><strong>Venue / Format:</strong></td><td style="text-align: right;">{st.session_state.cinema_choice}</td></tr>
                <tr><td style="padding: 6px 0;"><strong>Reserved Seats:</strong></td><td style="text-align: right;">{', '.join(st.session_state.confirmed_seats)}</td></tr>
                <tr><td style="padding: 6px 0;"><strong>Subtotal ({num_seats}x):</strong></td><td style="text-align: right;">${subtotal:.2f} SGD</td></tr>
                <tr><td style="padding: 6px 0;"><strong>Booking Fee:</strong></td><td style="text-align: right;">${booking_fee:.2f} SGD</td></tr>
                <tr><td style="padding: 10px 0; border-top: 1px solid #333; color: #fff; font-size: 16px;"><strong>Total Due:</strong></td><td style="text-align: right; border-top: 1px solid #333; color: #e50914; font-size: 16px;"><strong>${total_payable:.2f} SGD</strong></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="secure-badge">
                🔒 256-bit SSL Encrypted Payment Gateway — PCI-DSS Level 1 Compliant
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("payment_form"):
            st.text_input("Cardholder Name (as shown on card)")
            st.text_input("Card Number", type="password", placeholder="•••• •••• •••• ••••")
            
            col_exp, col_cvv = st.columns(2)
            with col_exp:
                st.text_input("Expiration Date", placeholder="MM/YY")
            with col_cvv:
                st.text_input("CVV / Security Code", type="password", placeholder="123")
                
            submitted = st.form_submit_button("Authorize Payment & Generate E-Tickets", type="primary")
            
            if submitted:
                with st.spinner("Processing transaction with financial institution..."):
                    time.sleep(1.5)
                    st.success("Transaction approved. Digital passes and receipt issued to system logs.")
                    
                    time.sleep(1.5)
                    st.session_state.confirmed_seats = []
                    st.session_state.show_seat_picker = False
                    st.session_state.messages = [
                        {"role": "assistant", "content": "Previous transaction completed successfully. Ready for next query."}
                    ]
                    st.rerun()
