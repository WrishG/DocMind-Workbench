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
    
    if trigger_name == "on_upload":
        # -> PHASE 3: Event-Driven Typing <-
        # We classify the document to know what we are dealing with.
        from vector_store import get_chunks_for_file
        from llm import classify_document
        
        chunks = await get_chunks_for_file(filename, max_chunks=3)
        if chunks:
            doc_type = classify_document(chunks)
            await db.documents.update_one(
                {"_id": doc_id},
                {"$set": {"document_type": doc_type}}
            )
            print(f"🧠 AI Classifier: Detected {filename} as '{doc_type}'")
    
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
            result = await execute_action(action.type, filename)
            final_output[action.type] = result
            
        # STEP 5: Logging
        log = WorkflowLog(
            workflow_id=workflow.id,
            document_id=doc_id,
            status="success",
            output=final_output
        )
        await db.workflow_logs.insert_one(log.model_dump(by_alias=True))
        # ---> NEW: Save to Cache <---
        # Map automation action names to our cache keys
        cache_updates = {}
        if "run_summary" in final_output:
            cache_updates["tasks.summarize"] = final_output["run_summary"]
        if "run_quiz" in final_output:
            cache_updates["tasks.quiz"] = final_output["run_quiz"]
            
        if cache_updates:
            await db.documents.update_one(
                {"_id": doc_id},
                {"$set": cache_updates}
            )
            print(f"⚡ Saved background automation results to Document Cache!")

        print(f"✅ Automation '{workflow.name}' completed and saved to DB!")
