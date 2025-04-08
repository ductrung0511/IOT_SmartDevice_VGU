import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.route(route="relay_on_trigger", auth_level=func.AuthLevel.ANONYMOUS)
def relay_on_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.event_hub_message_trigger(arg_name="azeventhub", event_hub_name="iotHUb",
                               connection="EVENT_HUB_CONNECTION") 
def iotHubTrigger(azeventhub: func.EventHubEvent):
    logging.info('Python EventHub trigger processed an event: %s',
                azeventhub.get_body().decode('utf-8'))

 # Endpoint=sb://ihsuprodosres004dednamespace.servicebus.windows.net/;SharedAccessKeyName=service;SharedAccessKey=YwW+wMjoVyEw2yxGuIzEHl0Yjgvz+3mobAIoTPC2G80=;EntityPath=iothub-ehub-soil-senso-55984687-6a753b17e4
    # Endpoint=sb://ihsuprodosres004dednamespace.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=GuWy8A5fwly3uB2mDnCf1RfZy+qCB/50RAIoTFpUidY=;EntityPath=iothub-ehub-soil-senso-55984687-6a753b17e4
@app.route(route="relay_off_trigger", auth_level=func.AuthLevel.ANONYMOUS)
def relay_off_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
