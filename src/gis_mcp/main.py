""" GIS MCP Server - Main entry point

This module implements an MCP server that connects LLMs to GIS operations using
Shapely and PyProj libraries, enabling AI assistants to perform geospatial operations
and transformations.
"""

import logging
import argparse
import sys
import os
from .mcp import gis_mcp
try:
    from .data import administrative_boundaries
except ImportError as e:
    administrative_boundaries = None
    import logging
    logging.warning(f"administrative_boundaries module could not be imported: {e}. Install with 'pip install gis-mcp[administrative-boundaries]' if you need this feature.")
try:
    from .data import climate
except ImportError as e:
    climate = None
    import logging
    logging.warning(f"climate module could not be imported: {e}. Install with 'pip install gis-mcp[climate]' if you need this feature.")
try:
    from .data import ecology
except ImportError as e:
    ecology = None
    import logging
    logging.warning(f"ecology module could not be imported: {e}. Install with 'pip install gis-mcp[ecology]' if you need this feature.")
try:
    from .data import movement
except ImportError as e:
    movement = None
    import logging
    logging.warning(f"movement module could not be imported: {e}. Install with 'pip install gis-mcp[movement]' if you need this feature.")

try:
    from .data import satellite_imagery
except ImportError as e:
    satellite_imagery = None
    import logging
    logging.warning(f"satellite_imagery module could not be imported: {e}. Install with 'pip install gis-mcp[satellite_imagery]' if you need this feature.")

try:
    from .data import land_cover
except ImportError as e:
    land_cover = None
    import logging
    logging.warning(f"land_cover module could not be imported: {e}. Install with 'pip install gis-mcp[land_cover]' if you need this feature.")

try:
    from .visualize import map_tool, web_map_tool
except ImportError as e:
    map_tool = None
    web_map_tool = None
    import logging
    logging.warning(f"Visualization modules could not be imported: {e}. Install with 'pip install gis-mcp[visualize]' if you need this feature.")


import warnings
warnings.filterwarnings('ignore')  # Suppress warnings for cleaner output

# Import tool modules to register MCP tools via decorators
from . import (
    geopandas_functions,
    shapely_functions,
    rasterio_functions,
    pyproj_functions,
    pysal_functions,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gis-mcp")

# Create FastMCP instance

def main():
    """Main entry point for the GIS MCP server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="GIS MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Get transport configuration from environment variables
    transport = os.getenv('GIS_MCP_TRANSPORT', 'stdio').lower()
    
    try:
        if transport == 'stdio':
            # Default stdio transport
            print("Starting GIS MCP server with STDIO transport...")
            logger.info("STDIO transport enabled (default)")
            gis_mcp.run()
        else:
            # HTTP transport configuration
            host = os.getenv('GIS_MCP_HOST', '0.0.0.0')
            port = int(os.getenv('GIS_MCP_PORT', '8080'))
            
            print(f"Starting GIS MCP server with {transport} transport on {host}:{port}")
            print(f"MCP endpoint will be available at: http://{host}:{port}/mcp")
            logger.info(f"{transport} transport enabled - {host}:{port}")
            
            gis_mcp.run(transport=transport, host=host, port=port)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
