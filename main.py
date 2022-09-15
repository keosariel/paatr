from paatr.factory import create_app
from fastapi import WebSocket
from paatr import logger

app = create_app()

@app.websocket("/services/apps/{app_id}/build_logs")
async def websocket_endpoint(websocket: WebSocket, app_id: str):
    logger.info("Accepting websocket connection for app %s", app_id)

    await websocket.accept()

    while True:
        try:
            # Wait for any message from the client
            await websocket.receive_text()
            # Send message to the client

            resp = {'value': 0}
            await websocket.send_json(resp)
        except Exception as e:
            logger.error("Error in websocket connection: %s", e)
            break

    logger.info("Closing websocket connection for app %s", app_id)