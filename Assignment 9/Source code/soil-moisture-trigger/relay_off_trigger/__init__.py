import logging
import os
import azure.functions as func
from azure.iot.hub import IoTHubRegistryManager, CloudToDeviceMethod

DEVICE_ID = "soil-device"  # Replace with your actual device ID

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('relay_off_trigger function was triggered.')

    try:
        # Build method request
        direct_method = CloudToDeviceMethod(method_name='relay_off', payload={})
        
        # Get connection string from environment
        registry_manager_connection_string = os.environ['REGISTRY_MANAGER_CONNECTION_STRING']
        registry_manager = IoTHubRegistryManager(registry_manager_connection_string)

        # Send method to device
        response = registry_manager.invoke_device_method(DEVICE_ID, direct_method)

        return func.HttpResponse(
            f"relay_off method invoked. Status: {response.status}, Payload: {response.payload}",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Failed to invoke method: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
