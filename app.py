
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import json
import asyncio
import os
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uvicorn

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP PiShock Server", version="1.0.0")

# Configuration depuis les variables d'environnement
PISHOCK_USERNAME = os.getenv("PISHOCK_USERNAME")
PISHOCK_APIKEY = os.getenv("PISHOCK_APIKEY")  
PISHOCK_CODE = os.getenv("PISHOCK_CODE")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
SCRIPT_NAME = os.getenv("SCRIPT_NAME", "MCP_Server")

PISHOCK_API_URL = "https://do.pishock.com/api/apioperate"

class ShockRequest(BaseModel):
    duration: int
    intensity: int

class VibrateRequest(BaseModel):
    duration: int
    intensity: int

class BeepRequest(BaseModel):
    duration: int

class MCPResponse(BaseModel):
    success: bool
    message: str
    operation: str
    id: Optional[str] = None

# Validation des variables d'environnement
@app.on_event("startup")
async def validate_environment():
    missing_vars = []
    if not PISHOCK_USERNAME:
        missing_vars.append("PISHOCK_USERNAME")
    if not PISHOCK_APIKEY:
        missing_vars.append("PISHOCK_APIKEY")
    if not PISHOCK_CODE:
        missing_vars.append("PISHOCK_CODE")
    if not MCP_AUTH_TOKEN:
        missing_vars.append("MCP_AUTH_TOKEN")
    
    if missing_vars:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

async def send_pishock_command(op: int, duration: int, intensity: Optional[int] = None):
    """Envoie une commande à l'API PiShock"""
    payload = {
        "Username": PISHOCK_USERNAME,
        "Apikey": PISHOCK_APIKEY,
        "Code": PISHOCK_CODE,
        "Name": SCRIPT_NAME,
        "Op": str(op),
        "Duration": str(duration)
    }
    
    if intensity is not None:
        payload["Intensity"] = str(intensity)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                PISHOCK_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            return response.text, response.status_code
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"PiShock API error: {str(e)}")

def create_mcp_response(result: Any, request_id: Optional[str] = None, error: Optional[str] = None):
    """Crée une réponse MCP-RPC standard"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    if error:
        response["error"] = {
            "code": -32000,
            "message": error
        }
    else:
        response["result"] = result
    
    return response

@app.get("/")
async def root():
    return {"message": "MCP PiShock Server", "version": "1.0.0", "mcp_path": "/mcp"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Route pour lister les méthodes disponibles
@app.get("/mcp")
async def mcp_info():
    return {
        "service": "MCP PiShock Server",
        "version": "1.0.0",
        "methods": ["SHOCK", "VIBRATE", "BEEP"],
        "protocol": "MCP 2025-06-18",
        "authentication": "Bearer Token required"
    }

# Route MCP principale - gère le protocole MCP complet
@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handler principal pour les requêtes MCP avec protocole complet"""
    try:
        # Log des headers
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Lire le body de la requête
        body = await request.body()
        logger.info(f"Request body: {body}")
        
        # Vérification de l'authentification
        authorization = request.headers.get("authorization")
        if not authorization:
            logger.warning("No authorization header found")
            return JSONResponse(
                status_code=401,
                content={"error": "Authorization header missing"}
            )
        
        if not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization format: {authorization}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid authorization format"}
            )
        
        token = authorization[7:]  # Remove "Bearer "
        if token != MCP_AUTH_TOKEN:
            logger.warning(f"Invalid token: {token}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token"}
            )
        
        # Si le body est vide, retourner les informations de service
        if not body:
            logger.info("Empty body, returning service info")
            return {
                "service": "MCP PiShock Server",
                "version": "1.0.0",
                "methods": ["SHOCK", "VIBRATE", "BEEP"]
            }
        
        # Parser le JSON
        try:
            body_text = body.decode('utf-8')
            logger.info(f"Body text: {body_text}")
            data = json.loads(body_text)
            logger.info(f"Parsed JSON: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JSONResponse(
                status_code=400,
                content=create_mcp_response(None, data.get("id") if 'data' in locals() else None, "Invalid JSON")
            )
        
        # Extraire les informations de la requête MCP
        method = data.get("method", "")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"Method: {method}, Params: {params}, ID: {request_id}")
        
        # Gestion des méthodes du protocole MCP
        if method == "initialize":
            # Réponse d'initialisation MCP
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "PiShock MCP Server",
                    "version": "1.0.0"
                }
            }
            return JSONResponse(content=create_mcp_response(result, request_id))
            
        elif method == "tools/list":
            # Liste des outils disponibles
            result = {
                "tools": [
                    {
                        "name": "SHOCK",
                        "description": "Send electric shock command to PiShock device",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "duration": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 15,
                                    "description": "Duration in seconds (1-15)"
                                },
                                "intensity": {
                                    "type": "integer", 
                                    "minimum": 1,
                                    "maximum": 100,
                                    "description": "Intensity level (1-100)"
                                }
                            },
                            "required": ["duration", "intensity"]
                        }
                    },
                    {
                        "name": "VIBRATE",
                        "description": "Send vibration command to PiShock device",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "duration": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "description": "Duration in seconds"
                                },
                                "intensity": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 100,
                                    "description": "Intensity level (1-100)"
                                }
                            },
                            "required": ["duration", "intensity"]
                        }
                    },
                    {
                        "name": "BEEP",
                        "description": "Send beep sound command to PiShock device",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "duration": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "description": "Duration in seconds"
                                }
                            },
                            "required": ["duration"]
                        }
                    }
                ]
            }
            return JSONResponse(content=create_mcp_response(result, request_id))
            
        elif method == "tools/call":
            # Appel d'un outil
            tool_name = params.get("name", "").upper()
            arguments = params.get("arguments", {})
            
            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            
            if tool_name == "SHOCK":
                duration = arguments.get("duration", 1)
                intensity = arguments.get("intensity", 5)
                
                if not (1 <= duration <= 15):
                    return JSONResponse(content=create_mcp_response(
                        None, request_id, "Duration must be between 1 and 15 seconds"
                    ))
                if not (1 <= intensity <= 100):
                    return JSONResponse(content=create_mcp_response(
                        None, request_id, "Intensity must be between 1 and 100"
                    ))
                
                response_text, status_code = await send_pishock_command(0, duration, intensity)
                success = status_code == 200 and "Operation Succeeded" in response_text
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"SHOCK command executed: {response_text.strip()}"
                        }
                    ],
                    "isError": not success
                }
                return JSONResponse(content=create_mcp_response(result, request_id))
                
            elif tool_name == "VIBRATE":
                duration = arguments.get("duration", 1)
                intensity = arguments.get("intensity", 30)
                
                if duration < 1:
                    return JSONResponse(content=create_mcp_response(
                        None, request_id, "Duration must be at least 1 second"
                    ))
                if not (1 <= intensity <= 100):
                    return JSONResponse(content=create_mcp_response(
                        None, request_id, "Intensity must be between 1 and 100"
                    ))
                
                response_text, status_code = await send_pishock_command(1, duration, intensity)
                success = status_code == 200 and "Operation Succeeded" in response_text
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"VIBRATE command executed: {response_text.strip()}"
                        }
                    ],
                    "isError": not success
                }
                return JSONResponse(content=create_mcp_response(result, request_id))
                
            elif tool_name == "BEEP":
                duration = arguments.get("duration", 1)
                
                if duration < 1:
                    return JSONResponse(content=create_mcp_response(
                        None, request_id, "Duration must be at least 1 second"
                    ))
                
                response_text, status_code = await send_pishock_command(2, duration)
                success = status_code == 200 and "Operation Succeeded" in response_text
                
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"BEEP command executed: {response_text.strip()}"
                        }
                    ],
                    "isError": not success
                }
                return JSONResponse(content=create_mcp_response(result, request_id))
                
            else:
                return JSONResponse(content=create_mcp_response(
                    None, request_id, f"Unknown tool: {tool_name}"
                ))
        
        else:
            logger.warning(f"Unknown method: {method}")
            return JSONResponse(content=create_mcp_response(
                None, request_id, f"Unknown method: {method}"
            ))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=create_mcp_response(
                None, request_id if 'request_id' in locals() else None, str(e)
            )
        )

# Routes individuelles pour compatibilité
@app.post("/mcp/SHOCK")
async def shock_direct(
    request: ShockRequest,
    authorization: Optional[str] = Header(None)
):
    """Route directe pour SHOCK (compatibilité)"""
    if not authorization or not authorization.startswith("Bearer ") or authorization[7:] != MCP_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    response_text, status_code = await send_pishock_command(0, request.duration, request.intensity)
    success = status_code == 200 and "Operation Succeeded" in response_text
    
    return {"success": success, "message": response_text.strip(), "operation": "SHOCK"}

@app.post("/mcp/VIBRATE")
async def vibrate_direct(
    request: VibrateRequest,
    authorization: Optional[str] = Header(None)
):
    """Route directe pour VIBRATE (compatibilité)"""
    if not authorization or not authorization.startswith("Bearer ") or authorization[7:] != MCP_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    response_text, status_code = await send_pishock_command(1, request.duration, request.intensity)
    success = status_code == 200 and "Operation Succeeded" in response_text
    
    return {"success": success, "message": response_text.strip(), "operation": "VIBRATE"}

@app.post("/mcp/BEEP")
async def beep_direct(
    request: BeepRequest,
    authorization: Optional[str] = Header(None)
):
    """Route directe pour BEEP (compatibilité)"""
    if not authorization or not authorization.startswith("Bearer ") or authorization[7:] != MCP_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    response_text, status_code = await send_pishock_command(2, request.duration)
    success = status_code == 200 and "Operation Succeeded" in response_text
    
    return {"success": success, "message": response_text.strip(), "operation": "BEEP"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
