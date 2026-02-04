from typing import List, Dict, Any, Optional
import reflex as rx
from ims.api.client import api_client

class FrameworkState(rx.State):
    """State for Frameworks page."""
    
    frameworks: List[Dict[str, Any]] = []
    mappings: List[Dict[str, Any]] = []
    is_loading: bool = False
    error: str = ""
    
    current_tab: str = "frameworks"

    async def load_data(self):
        """Load frameworks and mappings."""
        self.is_loading = True
        self.error = ""
        try:
            # Load Frameworks
            self.frameworks = await api_client.get_knowledge_entries(
                category="framework",
                limit=100
            )
            
            # Load Mappings (TwedeLijn)
            # Assuming 'mapping' or 'mapping_2nd_line' category
            self.mappings = await api_client.get_knowledge_entries(
                category="mapping",
                limit=100
            )
            
            # If no mappings found with "mapping", try "framework" subcategory just in case during dev
            if not self.mappings:
                 self.mappings = await api_client.get_knowledge_entries(
                    category="framework",
                    subcategory="mapping",
                    limit=100
                )

        except Exception as e:
            self.error = f"Fout bij laden van gegevens: {str(e)}"
            print(f"Error loading frameworks: {e}")
        finally:
            self.is_loading = False
            
    def set_tab(self, tab: str):
        self.current_tab = tab
