"""
Restaurant Crawl Planner Agent with LangChain and Groq
Generates personalized food crawl plans based on city, cuisine, and budget
"""

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from datetime import datetime, timedelta
import requests
import os
import sys
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Global chat history
chat_history = []

# =============================================================================
# CUSTOM TOOLS FOR RESTAURANT CRAWL PLANNING
# =============================================================================

@tool
def get_current_datetime() -> str:
    """Return current date & time in Indian Standard Time (IST)."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except ImportError:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return now.strftime("%Y-%m-%d %H:%M:%S (IST)")

@tool
def search_restaurants(city: str, cuisine: str, budget: str) -> str:
    """
    Search for restaurants in a city based on cuisine and budget preferences.
    
    Args:
        city: Name of the city
        cuisine: Type of cuisine (e.g., street food, vegan, fine dining, italian, chinese)
        budget: Budget level (low, medium, high)
    
    Returns:
        Restaurant recommendations with details
    """
    try:
        # Create a detailed search query
        query = f"best {cuisine} restaurants in {city} {budget} budget popular food places"
        
        # Use Tavily to search
        tavily_tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        
        results = tavily_tool.invoke({"query": query})
        
        if results:
            formatted_results = f"Restaurant search results for {cuisine} in {city} ({budget} budget):\n\n"
            if isinstance(results, list):
                for i, result in enumerate(results[:5], 1):
                    if isinstance(result, dict):
                        title = result.get('title', 'Restaurant')
                        content = result.get('content', '')
                        url = result.get('url', '')
                        formatted_results += f"{i}. {title}\n   {content[:200]}...\n   Source: {url}\n\n"
            return formatted_results
        else:
            return f"No specific results found, but {city} is known for great {cuisine} options!"
            
    except Exception as e:
        return f"Error searching restaurants: {str(e)}. Using general knowledge for {city}."

@tool
def get_cuisine_recommendations(cuisine_type: str) -> str:
    """
    Get popular dishes and recommendations for a specific cuisine type.
    
    Args:
        cuisine_type: Type of cuisine (e.g., street food, vegan, italian, indian)
    
    Returns:
        Popular dishes and what to try for that cuisine
    """
    cuisine_data = {
        "street food": "Popular dishes: Pani Puri, Vada Pav, Pav Bhaji, Chaat, Momos, Rolls, Samosas. Best time: Evening (5 PM - 9 PM). Budget: ₹50-200 per person.",
        "vegan": "Popular dishes: Buddha Bowls, Quinoa Salads, Veggie Wraps, Smoothie Bowls, Plant-based Burgers, Tofu Dishes. Best time: Lunch (12 PM - 2 PM) or Dinner (7 PM - 9 PM). Budget: ₹300-800 per person.",
        "fine dining": "Multi-course meals, Chef's specials, Wine pairings, Signature dishes, Tasting menus. Best time: Dinner (8 PM - 10 PM). Budget: ₹2000-5000+ per person. Reservation recommended.",
        "indian": "Popular dishes: Butter Chicken, Biryani, Tandoori items, Dal Makhani, Paneer dishes, Dosas, Thalis. Best time: Lunch (12 PM - 3 PM) or Dinner (7 PM - 10 PM). Budget varies by restaurant type.",
        "italian": "Popular dishes: Pizza, Pasta (Carbonara, Alfredo), Risotto, Tiramisu, Gelato. Best time: Lunch (12 PM - 3 PM) or Dinner (7 PM - 10 PM). Budget: ₹500-1500 per person.",
        "chinese": "Popular dishes: Dim Sum, Noodles, Fried Rice, Manchurian, Spring Rolls, Soups. Best time: Lunch (12 PM - 3 PM) or Dinner (7 PM - 10 PM). Budget: ₹300-1000 per person.",
        "japanese": "Popular dishes: Sushi, Ramen, Tempura, Teriyaki, Bento Boxes. Best time: Lunch (12 PM - 2 PM) or Dinner (7 PM - 9 PM). Budget: ₹800-2000 per person.",
        "thai": "Popular dishes: Pad Thai, Tom Yum Soup, Green Curry, Som Tam, Spring Rolls. Best time: Lunch or Dinner. Budget: ₹400-1200 per person.",
        "mediterranean": "Popular dishes: Hummus, Falafel, Shawarma, Greek Salad, Kebabs. Best time: Lunch or Dinner. Budget: ₹400-1200 per person."
    }
    
    cuisine_lower = cuisine_type.lower()
    for key in cuisine_data:
        if key in cuisine_lower:
            return f"Recommendations for {cuisine_type}:\n{cuisine_data[key]}"
    
    return f"General recommendations for {cuisine_type}: Explore local specialties, ask for chef's recommendations, and try signature dishes. Budget accordingly and check reviews online."

@tool
def calculate_crawl_timing(duration: str, num_stops: int) -> str:
    """
    Calculate timing for a food crawl with multiple stops.
    
    Args:
        duration: Duration type (half-day or full-day)
        num_stops: Number of restaurant stops
    
    Returns:
        Time schedule for the food crawl
    """
    try:
        if "half" in duration.lower():
            start_time = "11:00 AM"
            total_hours = 5
            activity = "Half-Day Food Crawl"
        else:
            start_time = "10:00 AM"
            total_hours = 10
            activity = "Full-Day Food Crawl"
        
        time_per_stop = total_hours / num_stops
        
        schedule = f"{activity} Schedule ({num_stops} stops):\n\n"
        current_hour = 10 if "full" in duration.lower() else 11
        current_min = 0
        
        for i in range(1, num_stops + 1):
            stop_duration = int(time_per_stop * 60)
            
            time_str = f"{current_hour:02d}:{current_min:02d}"
            am_pm = "AM" if current_hour < 12 else "PM"
            display_hour = current_hour if current_hour <= 12 else current_hour - 12
            if display_hour == 0:
                display_hour = 12
            
            schedule += f"Stop {i}: {display_hour}:{current_min:02d} {am_pm} (Duration: {stop_duration} mins)\n"
            
            # Add time
            current_min += stop_duration
            while current_min >= 60:
                current_min -= 60
                current_hour += 1
        
        return schedule
        
    except Exception as e:
        return f"Error calculating timing: {str(e)}"

# =============================================================================
# CREATE AGENT
# =============================================================================

def create_agent():
    """Initialize and return the restaurant crawl agent executor."""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=2048,
        timeout=60,
        max_retries=2
    )
    
    # Initialize Tavily search
    tavily_tool = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False
    )
    
    # Define all tools
    tools = [
        get_current_datetime,
        search_restaurants,
        get_cuisine_recommendations,
        calculate_crawl_timing,
        tavily_tool
    ]
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert food crawl planner and culinary guide. Your role is to create personalized restaurant crawl itineraries.

Your capabilities:
- Search for restaurants using the search_restaurants tool (provide city, cuisine, budget)
- Get cuisine-specific recommendations using get_cuisine_recommendations tool
- Calculate timing for food crawls using calculate_crawl_timing tool
- Use tavily_search_results_json for additional research
- Remember previous conversation context

When creating a food crawl plan:
1. First, search for restaurants based on user's preferences (city, cuisine, budget)
2. Get specific dish recommendations for the cuisine type
3. Calculate timing for the number of stops
4. Create a detailed itinerary with:
   - Restaurant names and locations (from search results)
   - Specific dishes to try at each stop
   - Timing for each stop
   - Budget estimates
   - Travel tips between stops

Budget Guidelines:
- Low budget: ₹200-500 per person for the entire crawl
- Medium budget: ₹500-1500 per person
- High budget: ₹1500-5000+ per person

Always provide:
- Clear time schedule
- Specific restaurant recommendations (from search results)
- Dish recommendations at each stop
- Approximate costs
- Any special tips (reservations needed, best time to visit, etc.)

Be enthusiastic, detailed, and help users discover amazing food experiences!"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        max_execution_time=120
    )
    
    return agent_executor

# =============================================================================
# CHAT FUNCTION
# =============================================================================

def chat(user_input: str, agent_executor):
    """
    Process user input and maintain chat history.
    
    Args:
        user_input: The user's message
        agent_executor: The agent executor instance
    
    Returns:
        The agent's response
    """
    global chat_history
    
    try:
        if chat_history is None:
            chat_history = []
        
        # Format chat history
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, tuple) and len(msg) == 2:
                role, content = msg
                if role == "human":
                    formatted_history.append(HumanMessage(content=content))
                elif role == "assistant" and content:
                    if isinstance(content, str):
                        formatted_history.append(AIMessage(content=content))
        
        if agent_executor is None:
            agent_executor = create_agent()
        
        # Prepare input
        input_data = {
            "input": user_input,
            "chat_history": formatted_history or []
        }
        
        # Run agent
        try:
            response = agent_executor.invoke(input_data)
            
            if response is None:
                output = "No response was generated. Please try again."
            elif isinstance(response, dict):
                output = response.get('output', '')
                if not output:
                    output = "I didn't get a proper response. Could you rephrase your question?"
            elif hasattr(response, 'output') and response.output is not None:
                output = str(response.output)
            else:
                output = str(response) if response is not None else "No response was generated."
            
            if not output or not isinstance(output, str):
                output = "I'm having trouble understanding. Could you rephrase your question?"
                
        except Exception as e:
            output = f"I encountered an error: {str(e)}. Could you please rephrase your question?"
        
        # Update chat history
        if output and output != 'No response generated':
            chat_history.append(("human", user_input))
            chat_history.append(("assistant", output))
        
        # Keep last 20 messages
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        return output if output else "I'm not sure how to respond to that. Could you rephrase?"
        
    except Exception as e:
        error_msg = f"Error in chat function: {str(e)}"
        print(error_msg)
        return "I'm sorry, I encountered an error processing your request. Please try again."

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🍽️ Restaurant Crawl Planner Agent")
    print("=" * 60)
    print("\n📋 Loading API keys from .env file...")
    print("\nRequired API Keys:")
    print("- GROQ_API_KEY (for LLM)")
    print("- TAVILY_API_KEY (for web search)")
    print("=" * 60)
    
    if not os.getenv("GROQ_API_KEY"):
        print("\n⚠️  GROQ_API_KEY not found in .env file!")
        print("\nPlease create a .env file with:")
        print("GROQ_API_KEY=gsk-your-groq-key-here")
        print("TAVILY_API_KEY=tvly-your-tavily-key-here")
        sys.exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("\n⚠️  TAVILY_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("✅ API keys loaded successfully!")
    
    print("\n🤖 Initializing agent...")
    try:
        agent_executor = create_agent()
        print("✅ Agent ready!\n")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")
        sys.exit(1)
    
    print("Chat with the Restaurant Crawl Planner (type 'quit' to exit):\n")
    print("Example: 'Plan a half-day street food crawl in Mumbai with low budget'\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 🍽️")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! 🍽️")
            break
        
        if user_input.lower() == 'clear':
            chat_history.clear()
            print("\n✅ Chat history cleared!\n")
            continue
        
        try:
            response = chat(user_input, agent_executor)
            print(f"\n🤖 Agent: {response}\n")
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.\n")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")