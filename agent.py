# This connects your SQLite database to Gemini through tools so it can pull your sleep or workout records on demand

import os
import streamlit as st
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from database import log_habit, get_recent_logs
from sg_calendar import check_upcoming_sg_events

# ==========================================
# 1. DEFINE HABIT & HEALTH TOOLS FOR GEMINI
# ==========================================

@tool
def record_daily_habit(category: str, value: float, notes: str) -> str:
    """
    Logs a daily habit entry. 
    Use this when the user tells you about their sleep, workouts, work hours, or daily activities.
    
    Args:
        category: The habit category ('sleep', 'workout', 'work', 'steps', etc.)
        value: Numeric value (e.g., hours of sleep, minutes of workout, step count)
        notes: Brief description or details of the activity
    """
    log_habit(category, value, notes)
    return f"Successfully logged {category}: {value} ({notes})."

@tool
def fetch_user_history(days: int = 7) -> str:
    """
    Retrieves the user's logged habits and activities from the database for the past N days.
    Use this to analyze their habits before giving lifestyle recommendations.
    
    Args:
        days: Number of past days to look up (default 7)
    """
    logs = get_recent_logs(days)
    if not logs:
        return "No habit logs found for this time period yet."
    
    formatted_logs = "Recent Habit Logs:\n"
    for date, category, value, notes in logs:
        formatted_logs += f"- Date: {date} | Category: {category} | Value: {value} | Notes: {notes}\n"
    
    return formatted_logs

@tool
def get_upcoming_singapore_events(days_ahead: int = 7) -> list:
    """Checks for upcoming public holidays and cultural events in Singapore for the next few days."""
    return check_upcoming_sg_events(days_ahead)


tools = [record_daily_habit, fetch_user_history, get_upcoming_singapore_events]
tool_map = {t.name: t for t in tools}

@st.cache_resource
def get_habit_model():
    # Bind the tools to Gemini 3.6 Flash
    return ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2).bind_tools(tools)

model = get_habit_model()