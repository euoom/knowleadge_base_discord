from fastapi import FastAPI, Request
from pydantic import BaseModel

class Interaction(BaseModel):
    type: int

app = FastAPI()

@app.post("/interactions")
async def handle_interactions(interaction: Interaction):
    if interaction.type == 1:
        return {"type": 1}
    return {"message": "Unhandled interaction type"}

@app.get("/")
def read_root():
    return {"message": "Knowleadge Base Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
