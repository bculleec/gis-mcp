# Getting Started

This guide helps you install and run the GIS MCP Server quickly using pip (with uv) and shows how to connect it to your IDE/client.

### Prerequisites

- Python 3.10+
- Internet access to install packages

### Install via pip (with uv)

1. Create a virtual environment:

```bash
pip install uv
uv venv --python=3.10
```

2. Install the package:

```bash
uv pip install gis-mcp
```

3. Run the server:

```bash
gis-mcp
```

By default, the server runs in **STDIO transport mode**, which is ideal for local development and integration with Claude Desktop or Cursor IDE.

You can also run the server in **HTTP transport mode** for network deployments:

```bash
export GIS_MCP_TRANSPORT=http
export GIS_MCP_PORT=8080
gis-mcp
```

For more details on transport modes (STDIO vs HTTP), see the [HTTP Transport Configuration](http-transport.md) documentation.

### Connect to an MCP client

Claude Desktop (Windows):

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\Users\\YourUsername\\.venv\\Scripts\\gis-mcp",
      "args": []
    }
  }
}
```

Claude Desktop (Linux/Mac):

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": []
    }
  }
}
```

Cursor IDE (Windows) – `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\Users\\YourUsername\\.venv\\Scripts\\gis-mcp",
      "args": []
    }
  }
}
```

Cursor IDE (Linux/Mac) – `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": []
    }
  }
}
```

This video teaches you the installation of GIS MCP Server on your windows and Claude Desktop:

<iframe width="560" height="315" src="https://www.youtube.com/embed/1u_ra1Wp4es" frameborder="0" allowfullscreen></iframe>

Notes

- Replace `YourUsername` with your actual username
- Restart your IDE after adding configuration

### Optional Features & Extras

GIS MCP Server supports several optional features for specialized workflows. You can install these extras using pip with square brackets, e.g.:

```bash
uv pip install "gis-mcp[climate]"
```

Available extras:

- **climate**: For climate data access and processing (installs `cdsapi`)
- **ecology**: For ecological and biodiversity data (installs `pygbif`)
- **administrative-boundaries**: For working with global administrative boundaries (installs `pygadm`)
- **movement**: For movement and network analysis (installs `osmnx`)
- **satellite-imagery**: For searching and processing satellite imagery (installs `pystac-client`, `planetary-computer`, `xarray`, `stackstac`, `requests`)
- **land-cover**: For land cover data workflows (same as satellite-imagery)
- **all**: Installs all optional dependencies for full functionality

Example to install with multiple extras:

```bash
uv pip install "gis-mcp[climate,ecology,movement]"
```

See the `pyproject.toml` or documentation for the full list of extras and their included packages.

For more information on fetching external datasets (climate, ecology, movement, satellite imagery, and more), see the [Data Gathering guide](data-gathering/README.md).

### Next steps

- Explore the API Reference in the sidebar (Shapely, PyProj, GeoPandas, Rasterio, PySAL)
- Check Installations → Developers for editable installs
