"""
This script creates your chat interface. 
You can type things like "I slept 6 hours last night and went for a 45-minute Zone 4 run" or 
"How have my habits been this week, and what should I improve?", 
and Gemini will automatically log your data or check your history to give you personalized health and lifestyle advice.
"""


import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agent import model, tool_map


# ==========================================
# PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Personal Habit & Health Co-Pilot", page_icon="🌱", layout="centered")

st.markdown("""
    <div style='text-align: center; padding: 10px; border-bottom: 2px solid #2ecc71; margin-bottom: 20px;'>
        <h1 style='color: #2ecc71;'>🌱 Habit & Health Co-Pilot</h1>
        <p style='color: #888;'>Track your daily habits, analyze your routines, and get personalized lifestyle coaching.</p>
    </div>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm your personal habit tracker. Tell me about your day—such as how many hours you slept, your workouts, or work hours—and I'll log them. You can also ask for recommendations whenever you're ready!"
        }
    ]

# ==========================================
# RENDER CHAT HISTORY
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# HANDLE USER INPUT & AGENT EXECUTION
# ==========================================
if user_prompt := st.chat_input("Tell me about your sleep, workout, or ask for advice..."):
    # 1. Append and render user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        
    # 2. Generate assistant response using LangChain and tools
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your habits..."):
            try:
                system_instruction = (
                    "You are a supportive, insightful personal health and wellness co-pilot. "
                    "Your job is to track the user's daily habits using your logging tools and review their "
                    "history when they ask for advice or recommendations. "
                    "Be encouraging, practical, and proactive. If they report low sleep or lack of activity, "
                    "gently suggest adjustments to help them stay healthy and balanced."
                )

                lc_messages = [("system", system_instruction)]

                for m in st.session_state.messages:
                    if m["role"] == "user":
                        lc_messages.append(HumanMessage(content=m["content"]))
                    else:
                        lc_messages.append(AIMessage(content=m["content"]))
                
                response = model.invoke(lc_messages)
                
                # Extract text response
                if isinstance(response.content, list):
                    output_text = "".join([part.get("text", "") for part in response.content if isinstance(part, dict)])
                else:
                    output_text = response.content or ""

                # Execute any tool calls requested by Gemini
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        t_name = tool_call["name"]
                        t_args = tool_call["args"]
                        tool_result = tool_map[t_name].invoke(t_args)
                        output_text += f"\n\n*(System Log: {tool_result})*"
                
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")