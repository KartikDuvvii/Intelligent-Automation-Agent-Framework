from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
import time

# Import the agent
from core.agents.autonomous_agent import AutonomousAgent

app = FastAPI(
    title="Intelligent Automation Agent API",
    description="REST interface for triggering and monitoring autonomous automation tasks.",
    version="1.0.0"
)

# Shared agent instance (could be moved to a dependency injection pattern)
agent = AutonomousAgent()

# Store task status in-memory for this example
tasks_db: Dict[str, Dict] = {}

class AutomationRequest(BaseModel):
    task_description: str
    metadata: Optional[Dict] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    timestamp: float

def execute_task_background(task_id: str, description: str):
    """Executes the agent task in the background."""
    tasks_db[task_id]["status"] = "processing"
    try:
        result = agent.run(description)
        tasks_db[task_id]["result"] = result
        tasks_db[task_id]["status"] = "completed"
    except Exception as e:
        tasks_db[task_id]["result"] = f"Error: {str(e)}"
        tasks_db[task_id]["status"] = "failed"
    tasks_db[task_id]["timestamp"] = time.time()

@app.post("/tasks", response_model=TaskStatus)
async def create_task(request: AutomationRequest, background_tasks: BackgroundTasks):
    """Triggers a new automation task."""
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "result": None,
        "timestamp": time.time()
    }
    
    background_tasks.add_task(execute_task_background, task_id, request.task_description)
    
    return tasks_db[task_id]

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Retrieves the status and result of a specific task."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.get("/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """Lists all recent automation tasks."""
    return list(tasks_db.values())

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "operational", "agent_ready": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
