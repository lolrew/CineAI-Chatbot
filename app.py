import streamlit as st

# ==========================================
# 1. PAGE CONFIG MUST BE THE ABSOLUTE FIRST COMMAND
# ==========================================
st.set_page_config(
    page_title="LalaAI | Habit & Health Coach",
    # Option A: Use a clean professional SVG icon URL
    page_icon="https://api.iconify.design/lucide:activity.svg?color=%2310b981",
    # Option B: Or use a clean professional standard emoji like a chart or robot if preferred: "📊" or "🤖"
    layout="centered"
)

# Now import everything else AFTER set_page_config
from langchain_core.messages import HumanMessage, AIMessage
from agent import model, tool_map

# ==========================================
# 2. UI STYLING & HEADER
# ==========================================
st.markdown("""
    <div style='text-align: center; padding: 10px; border-bottom: 2px solid #2ecc71; margin-bottom: 20px;'>
        <h1 style='color: #2ecc71;'>"📊 LalaAI Habit & Health Coach"</h1>
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
                    "Be conversational, encouraging, and practical. When a user provides data, acknowledge it "
                    "warmly and confirm it has been logged. When they ask for advice, use your tools to check their "
                    "history, then talk directly to them like an expert coach. "
                    "CRITICAL STYLE RULE: Keep your replies short, punchy, and conversational (1-3 sentences max) "
                    "unless the user explicitly asks for a detailed plan, schedule, or long breakdown. "
                    "TABLE RULE: Whenever the user asks for a training schedule, routine, or multi-day plan, "
                    "always format the output as a clean Markdown table with clear columns (e.g., Day, Focus, Activity, Notes)."
                )

                lc_messages = [("system", system_instruction)]

                for m in st.session_state.messages:
                    if m["role"] == "user":
                        lc_messages.append(HumanMessage(content=m["content"]))
                    else:
                        lc_messages.append(AIMessage(content=m["content"]))
                
                # First invoke to see if model wants to call tools or talk
                response = model.invoke(lc_messages)
                
                output_text = ""
                
                # If the model wants to call tools, execute them and feed results back for a final conversational reply
                if response.tool_calls:
                    # Append the AI's tool call message context
                    lc_messages.append(response)
                    
                    for tool_call in response.tool_calls:
                        t_name = tool_call["name"]
                        t_args = tool_call["args"]
                        tool_result = tool_map[t_name].invoke(t_args)
                        
                        # Add tool execution result back to message history for Gemini to read
                        from langchain_core.messages import ToolMessage
                        lc_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
                    
                    # Second invoke: Let Gemini read the tool results and write a natural, conversational response back to you
                    final_response = model.invoke(lc_messages)
                    output_text = final_response.content if isinstance(final_response.content, str) else "".join([p.get("text", "") for p in final_response.content if isinstance(p, dict)])
                else:
                    output_text = response.content if isinstance(response.content, str) else "".join([p.get("text", "") for p in response.content if isinstance(p, dict)])
                
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")