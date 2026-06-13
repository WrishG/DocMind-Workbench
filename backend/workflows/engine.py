# backend/workflows/engine.py
from models import WorkflowTemplate, WorkflowLog
from database import db
from workflows.actions import execute_action

async def process_trigger(trigger_name: str, document_metadata: dict):
    """
    This function is fired automatically when an event occurs (e.g., an upload).
    """
    filename = document_metadata.get("filename", "")
    doc_id = document_metadata.get("id", "")
    
    # STEP 1: Query MongoDB for all workflows listening for this specific trigger.
    # If trigger_name is "on_upload", we fetch all upload automations.
    cursor = db.workflows.find({"trigger": trigger_name})
    workflows = await cursor.to_list(length=100)
    
    # STEP 2: Loop through every automation we found
    for wf_data in workflows:
        workflow = WorkflowTemplate(**wf_data) # Convert JSON back to Pydantic object
        
        # STEP 3: Condition Checking
        # If the user only wants this to run on files containing "resume", we check that here.
        should_run = True
        for condition in workflow.conditions:
            if condition.field == "filename" and condition.operator == "contains":
                if condition.value.lower() not in filename.lower():
                    should_run = False # It failed the check. Abort!
        
        if not should_run:
            continue # Skip to the next workflow
            
        # STEP 4: Execution
        # If we passed the conditions, execute the AI actions!
        final_output = {}
        for action in workflow.actions:
            print(f"⚙️ Automation Engine: Running '{action.type}' for {filename}")
            
            # Call our switchboard file
            result = execute_action(action.type, filename)
            final_output[action.type] = result
            
        # STEP 5: Logging
        # Never run a background task without saving a log, or the user won't know it finished.
        log = WorkflowLog(
            workflow_id=workflow.id,
            document_id=doc_id,
            status="success",
            output=final_output
        )
        await db.workflow_logs.insert_one(log.model_dump(by_alias=True))
        print(f"✅ Automation '{workflow.name}' completed and saved to DB!")
