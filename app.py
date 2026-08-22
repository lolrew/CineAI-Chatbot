import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agent import model, tool_map

# ==========================================
# 1. PAGE CONFIG MUST BE THE ABSOLUTE FIRST COMMAND
# ==========================================
st.set_page_config(
    page_title="LalaAI | Habit & Health Coach",
    page_icon="https://api.iconify.design/lucide:activity.svg?color=%2310b981",
    layout="centered"
)

# Cache resource to eliminate reload lag
@st.cache_resource
def get_cached_model():
    return model, tool_map

cached_model, cached_tool_map = get_cached_model()

# ==========================================
# 2. SIDEBAR - TOKEN & QUOTA MONITOR
# ==========================================
if "total_tokens_used" not in st.session_state:
    st.session_state.total_tokens_used = 0

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

with st.sidebar:
    st.header("📊 Usage & Quota")
    st.metric("Requests Today (Est.)", f"{st.session_state.request_count} / 20")
    st.progress(min(st.session_state.request_count / 20.0, 1.0))
    st.metric("Total Tokens Consumed", st.session_state.total_tokens_used)
    st.info("Free tier limit is 20 requests/day.")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! I'm your personal habit tracker. Tell me about your day—such as how many hours you slept, your workouts, or work hours—and I'll log them."
        }]
        st.rerun()

# ==========================================
# 3. UI STYLING & HEADER
# ==========================================
st.markdown("""
    <div style='text-align: center; padding: 10px; border-bottom: 2px solid #2ecc71; margin-bottom: 20px;'>
        <h1 style='color: #2ecc71;'>LalaAI Coach</h1>
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
# 4. HANDLE USER INPUT & AGENT EXECUTION
# ==========================================
if user_prompt := st.chat_input("Tell me about your sleep, workout, or ask for advice..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        
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
                
                # Increment request counter
                st.session_state.request_count += 1
                
                # Invoke model
                response = cached_model.invoke(lc_messages)
                output_text = ""
                
                # Track usage metadata if available from response
                if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
                    usage = response.response_metadata["token_usage"]
                    st.session_state.total_tokens_used += usage.get("total_tokens", 0)

                if response.tool_calls:
                    lc_messages.append(response)

                    for tool_call in response.tool_calls:
                        t_name = tool_call["name"]
                        t_args = tool_call["args"]

                        try:
                            tool_result = cached_tool_map[t_name].invoke(t_args)
                        except Exception as tool_err:
                            tool_result = f"Error executing tool {t_name}: {tool_err}"

                        from langchain_core.messages import ToolMessage
                        lc_messages.append(
                            ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                        )

                    final_response = cached_model.invoke(lc_messages)
                    
                    if hasattr(final_response, "response_metadata") and "token_usage" in final_response.response_metadata:
                        usage = final_response.response_metadata["token_usage"]
                        st.session_state.total_tokens_used += usage.get("total_tokens", 0)

                    output_text = (
                        final_response.content
                        if isinstance(final_response.content, str)
                        else "".join([p.get("text", "") for p in final_response.content if isinstance(p, dict)])
                    )
                else:
                    output_text = (
                        response.content
                        if isinstance(response.content, str)
                        else "".join([p.get("text", "") for p in response.content if isinstance(p, dict)])
                    )
                
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")