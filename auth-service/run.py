#!/usr/bin/env python
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # In production, use 0.0.0.0 to accept all connections
    # In development, you can keep 127.0.0.1
    host = "0.0.0.0" if os.environ.get("RENDER") else "127.0.0.1"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.environ.get("ENVIRONMENT") == "development"
    )
