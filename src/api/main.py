from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from rag.generator import generate_response

app = FastAPI(title="Medical Symptom API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@app.get("/query")
async def get_medical_response(symptoms: str = Query(...), is_follow_up: bool = Query(False)):
    """
    Get a medical response based on input symptoms.
    Example: /query?symptoms=body%20ache&is_follow_up=false
    """
    if not symptoms:
        return JSONResponse(status_code=400, content={"error": "Symptoms parameter is required"})

    try:
        logger.info(f"Query: '{symptoms}', is_follow_up: {is_follow_up}")
        response = generate_response(symptoms, is_follow_up)
        
        # Handle both string and dict responses from generator.py
        if isinstance(response, dict):
            return {
                "symptoms": symptoms,
                "response": response.get("response", ""),
                "conditions": response.get("conditions", [])
            }
        else:
            return {
                "symptoms": symptoms,
                "response": response,
                "conditions": []
            }
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    """Check the API health status."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
