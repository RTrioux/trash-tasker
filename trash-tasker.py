import ovh
import datetime
import pandas as pd
import json
import logging
import sys
import os

client_get = ovh.Client(config_file="ovh-get.conf")
client_send = ovh.Client(config_file="ovh.conf")
sms_services = client_get.get("/sms")

# Choose a service (example: 'sms-xxxxxx')
sms_service_name = sms_services[0]  # Replace with your SMS service ID

no_sms = False  # Debug purpose
redirect_sms = False  # Debug purpose
number_debug = "+33600000000"  # Debug purpose


log_file = "trash-tasker-dev.log"
if os.getenv("TRASH_TASKER_ENV") == "RELEASE":
    log_file = "/var/log/trash-tasker.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def send_sms(number: str, message: str):

    if no_sms:
        logger.info(f"Sending SMS to ({number}): {message}")
        return
    if redirect_sms:
        number = number_debug

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
        logger.debug(response)
    except ovh.exceptions.APIError as e:
        logger.error(f"An error occurred: {e}")


def check_schedule_directory(schedule_path, repository_path):
    df = pd.read_csv(schedule_path, sep=",", na_values="")
    df = df.where(pd.notnull(df), None)  # Replace NaN with None

    status_ok = True

    with open(repository_path, "r") as file:
        rep = json.load(file)

        for key in df["name"]:

            if key is None:
                continue

            if key not in rep:
                status_ok = False
                logger.error(f"User {key} not found in directory")
                continue

            if isinstance(rep[key]["name"], str) or isinstance(rep[key]["phone"], str):
                status_ok = False
                logger.error(f"User {key} has name or phone number as string, it should be a list")
                continue

            if "name" not in rep[key] or "phone" not in rep[key]:
                status_ok = False
                logger.error(f"User {key} does not have name or phone number")
                continue

            if len(rep[key]["name"]) != len(rep[key]["phone"]):
                status_ok = False
                logger.error(f"User {key} has different number of names and phone numbers")
                continue

    return status_ok


def send_test_sms_to_all_users(directory: dict):

    for user_key in directory:
        users = directory[user_key]
        for name, number in zip(users["name"], users["phone"]):
            message = f"Bonjour {name} ceci est un message de test pour les poubelles"
            send_sms(number, message)


if __name__ == "__main__":

    if check_schedule_directory("schedule.csv", "directory.json") is False:
        logger.error("Some errors were found in the schedule or directory file")
        exit(1)
    td = datetime.datetime.now()
    _, week, day = td.isocalendar()

    df = pd.read_csv("schedule.csv", sep=",", na_values="")
    df = df.where(pd.notnull(df), None)  # Replace NaN with None
    user_key = df["name"][week - 1]

    with open("directory.json", "r") as file:
        rep = json.load(file)
        glass_notification = df["glass"][week - 1] is not None
        message_glass = "ET VERRES" if glass_notification else ""

        for name, number in zip(rep[user_key]["name"], rep[user_key]["phone"]):
            message = f"RAPPEL POUBELLES {message_glass}: Bonjour {name:.12} c'est votre tour pour les poubelles ce weekend"
            send_sms(number, message)
