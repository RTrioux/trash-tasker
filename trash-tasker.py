import ovh
import datetime
import pandas as pd
import json

client_get = ovh.Client(config_file="ovh.conf")
client_send = ovh.Client(config_file="ovh_send.conf")
sms_services = client_get.get("/sms")

# Choose a service (example: 'sms-xxxxxx')
sms_service_name = sms_services[0]  # Replace with your SMS service ID


def send_sms(number: str, message: str):
    # Prepare SMS parameters
    sms_params = {
        "message": message,  # Message content
        "receivers": [number],  # Replace with the recipient's phone number
        "senderForResponse": True,  # On accepte les réponses sinon on a besoin d'un sender
    }
    # Send SMS
    try:
        # Your API calls here
        response = client_send.post(f"/sms/{sms_service_name}/jobs", **sms_params)
        print(response)
    except ovh.exceptions.APIError as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    td = datetime.datetime.now()
    _, week, day = td.isocalendar()

    df = pd.read_csv("schedule.csv", sep=",", na_values="")
    df = df.where(pd.notnull(df), None)  # Replace NaN with None
    name = df["Nom"][week - 1]

    with open("directory.json", "r") as file:
        rep = json.load(file)
        number = rep[name]["phone"]
        glass_notification = df["Verre"][week - 1] is not None
        message_glass = "ET VERRES" if glass_notification else ""
        message = f"RAPPEL POUBELLES {message_glass}: Bonjour {name:.12} c'est votre tour pour les poubelles ce weekend."

        send_sms(rep[name]["phone"], message)
