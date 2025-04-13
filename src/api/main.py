from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Medical Symptom API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for dev/testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/query")
async def get_medical_response(symptoms: str):
    """
    Get a medical response based on input symptoms.
    Example: /query?symptoms=itching,fatigue,yellowish skin
    """
    if not symptoms:
        return JSONResponse(status_code=400, content={"error": "Symptoms parameter is required"})

    # Placeholder response (to be replaced with RAG logic)
    try:
        # Simulate processing delay
        import time
        time.sleep(1)
        
        placeholder_response = f"Analyzing symptoms: {symptoms}. Possible condition: Jaundice (based on yellowish skin, itching). Consult a doctor."
        placeholder_conditions = [
            {"condition": "Jaundice", "text": "Yellowish skin, itching, fatigue..."},
            {"condition": "Hepatitis", "text": "Fatigue, abdominal pain..."}
        ]

        return {
            "symptoms": symptoms,
            "response": placeholder_response,
            "conditions": placeholder_conditions
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    """Check the API health status."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)