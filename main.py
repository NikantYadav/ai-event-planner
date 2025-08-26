from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import json

from api.places import GooglePlacesAPI
from api.place_embeddings import convert_places_to_embeddings
from db.place_embeddings_store import store_places_to_tidb
from utils.logger import get_logger

logger = get_logger(__name__)

class EventPlannerState:
    """State for the AI Event Planner agent"""
    def __init__(self):
        self.query: str = ""
        self.places_data: List[Dict[str, Any]] = []
        self.embeddings_data: List[tuple] = []
        self.stored_count: int = 0
        self.error: str = ""

def search_places_node(state: EventPlannerState) -> EventPlannerState:
    """Node to search for places using Google Places API"""
    logger.info(f"Searching for places with query: {state.query}")
    
    try:
        places_api = GooglePlacesAPI()
        places_data = places_api.search_places_with_details(state.query)
        
        state.places_data = places_data
        logger.info(f"Found {len(places_data)} places")
        
    except Exception as e:
        state.error = f"Error searching places: {str(e)}"
        logger.error(state.error)
    
    return state

def generate_embeddings_node(state: EventPlannerState) -> EventPlannerState:
    """Node to generate embeddings for the places"""
    if state.error or not state.places_data:
        return state
        
    logger.info(f"Generating embeddings for {len(state.places_data)} places")
    
    try:
        embeddings_data = convert_places_to_embeddings(state.places_data)
        state.embeddings_data = embeddings_data
        logger.info(f"Generated {len(embeddings_data)} embeddings")
        
    except Exception as e:
        state.error = f"Error generating embeddings: {str(e)}"
        logger.error(state.error)
    
    return state

def store_embeddings_node(state: EventPlannerState) -> EventPlannerState:
    """Node to store embeddings in TiDB vector database"""
    if state.error or not state.embeddings_data:
        return state
        
    logger.info(f"Storing {len(state.embeddings_data)} embeddings in TiDB")
    
    try:
        successful, failed = store_places_to_tidb(state.places_data)
        state.stored_count = successful
        logger.info(f"Successfully stored {successful} embeddings, {failed} failed")
        
    except Exception as e:
        state.error = f"Error storing embeddings: {str(e)}"
        logger.error(state.error)
    
    return state

def should_continue(state: EventPlannerState) -> str:
    """Conditional edge to determine if we should continue or end"""
    if state.error:
        return "error"
    elif not state.places_data:
        return "no_places"
    else:
        return "continue"

def create_event_planner_graph():
    """Create the LangGraph workflow for the AI Event Planner"""
    
    # Create the graph
    workflow = StateGraph(EventPlannerState)
    
    # Add nodes
    workflow.add_node("search_places", search_places_node)
    workflow.add_node("generate_embeddings", generate_embeddings_node)
    workflow.add_node("store_embeddings", store_embeddings_node)
    
    # Set entry point
    workflow.set_entry_point("search_places")
    
    # Add edges
    workflow.add_conditional_edges(
        "search_places",
        should_continue,
        {
            "continue": "generate_embeddings",
            "no_places": END,
            "error": END
        }
    )
    
    workflow.add_edge("generate_embeddings", "store_embeddings")
    workflow.add_edge("store_embeddings", END)
    
    return workflow.compile()

def run_event_planner(query: str):
    """Run the AI Event Planner with a search query"""
    logger.info(f"Starting AI Event Planner for query: {query}")
    
    # Create the graph
    app = create_event_planner_graph()
    
    # Initialize state
    initial_state = EventPlannerState()
    initial_state.query = query
    
    # Run the workflow
    try:
        final_state = app.invoke(initial_state)
        
        # Print results
        if final_state.error:
            print(f"❌ Error: {final_state.error}")
        elif not final_state.places_data:
            print("❌ No places found for the query")
        else:
            print(f"✅ Successfully processed {len(final_state.places_data)} places")
            print(f"✅ Generated {len(final_state.embeddings_data)} embeddings")
            print(f"✅ Stored {final_state.stored_count} embeddings in TiDB")
            
            # Show some sample places
            print("\n📍 Sample places found:")
            for i, place in enumerate(final_state.places_data[:3]):
                name = place.get('displayName', {}).get('text', 'Unknown')
                place_type = place.get('primaryType', 'Unknown type')
                print(f"  {i+1}. {name} ({place_type})")
                
    except Exception as e:
        logger.error(f"Error running event planner: {e}")
        print(f"❌ Error running event planner: {e}")

if __name__ == "__main__":
    # Example usage
    query = input("Enter your event planning query (e.g., 'decoration vendors in Gurugram'): ").strip()
    
    if not query:
        query = "decoration vendors in Gurugram"
        print(f"Using default query: {query}")
    
    run_event_planner(query)
   
