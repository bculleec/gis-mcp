# Docker Installation

### Install via Docker

GIS MCP Server can be run using Docker, which provides an isolated environment with all dependencies pre-installed.

**Important:** Both `Dockerfile` and `Dockerfile.local` have **HTTP transport mode enabled by default**. The server runs on port `9010` and is accessible at `http://localhost:9010/mcp`.

#### Using Dockerfile

The main `Dockerfile` installs the package from PyPI:

1. Build the Docker image:

```bash
docker build -t gis-mcp .
```

2. Run the container (HTTP mode is enabled by default):

```bash
docker run -p 9010:9010 gis-mcp
```

The server will be available at `http://localhost:9010/mcp` in HTTP transport mode.

#### Using Dockerfile.local

The `Dockerfile.local` installs the package from local source files (useful for development or custom builds):

1. Build the Docker image:

```bash
docker build -f Dockerfile.local -t gis-mcp:local .
```

2. Run the container (HTTP mode is enabled by default):

```bash
docker run -p 9010:9010 gis-mcp:local
```

The server will be available at `http://localhost:9010/mcp` in HTTP transport mode.

#### Environment Variables

Both Dockerfiles set the following environment variables by default:

- `GIS_MCP_TRANSPORT=http` - HTTP transport mode is enabled by default
- `GIS_MCP_HOST=0.0.0.0` - HTTP server host
- `GIS_MCP_PORT=9010` - HTTP server port

You can override these by setting environment variables when running the container.

#### Running in STDIO Mode

To use STDIO transport instead of HTTP, override the transport environment variable:

```bash
docker run -e GIS_MCP_TRANSPORT=stdio gis-mcp
```

#### Running in HTTP Mode (Default)

HTTP transport is the default in Docker. Simply expose the port:

```bash
docker run -p 9010:9010 gis-mcp
```

Or with custom host and port:

```bash
docker run -e GIS_MCP_HOST=0.0.0.0 -e GIS_MCP_PORT=9000 -p 9000:9000 gis-mcp
```

#### Client Configuration

For HTTP transport mode, configure your MCP client to connect to:

```
http://localhost:9010/mcp
```

For STDIO transport mode, configure your client to run the Docker container:

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "docker",
      "args": ["run", "-i", "gis-mcp"]
    }
  }
}
```

#### Notes

- The Dockerfiles use Python 3.12 and include all system dependencies (GDAL, PROJ, GEOS)
- Both `Dockerfile` and `Dockerfile.local` install the package with all extras (`[all]`)
- **HTTP transport mode is enabled by default** in both Dockerfiles
- The default port is `9010` in both Dockerfiles
- For production deployments, consider using specific image tags instead of `latest`
- For more details on transport modes, see the [HTTP Transport Configuration](../http-transport.md) documentation

