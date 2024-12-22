#!/usr/bin/env python3

import argparse
import ovh
import datetime
import pandas as pd
import json
import logging
import sys
import os
import time


client_get = ovh.Client(config_file="ovh-get.conf")
client_send = ovh.Client(config_file="ovh.conf")

# Logging

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


# Profile
no_sms = False  # Debug purpose
redirect_sms = False  # Debug purpose
number_debug = "+33600000000"  # Debug purpose
cc_sms = False  # Debug purpose

try:
    with open("profile.json", "r") as file:
        profile = json.load(file)
        no_sms = profile["no_sms"]
        redirect_sms = profile["redirect_sms"]
        number_debug = profile["number_debug"]
        cc_sms = profile["cc_sms"]
except FileNotFoundError:
    logger.warning("Profile file not found, using default values")
except KeyError:
    logger.error("Profile file is not correctly formatted")


def send_sms(number: str, message: str):

    if no_sms:
        logger.info(f"[TEST] Sending SMS to ({number}): {message}")
        return
    if redirect_sms:
        number = number_debug

    logger.info(f"Sending SMS to ({number}): {message}")

    # Prepare SMS parameters
    sms_params = {
        "message": message,  # Message content
        "receivers": [number],  # Replace with the recipient's phone number
        "senderForResponse": True,  # On accepte les réponses sinon on a besoin d'un sender
    }
    # Send SMS
    n_retry = 3
    retry_time = 5
    for i in range(n_retry):
        try:
            sms_services = client_get.get("/sms")  # Get SMS services
            sms_service_name = sms_services[0]  # Choose a service (example: 'sms-xxxxxx')
            # Your API calls here
            response = client_send.post(f"/sms/{sms_service_name}/jobs", **sms_params)
            logger.debug(response)
            break
        except ovh.exceptions.APIError as e:
            logger.error(f"An error occurred: retry n°{i}: {e}")
            time.sleep(retry_time)


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


def show_schedule():

    from rich.console import Console
    from rich.table import Table

    # Console
    console = Console()

    td = datetime.datetime.now()
    _, week, _ = td.isocalendar()

    df = pd.read_csv("schedule.csv", sep=",", na_values="")
    df = df.where(pd.notnull(df), None)  # Replace NaN with None

    table = Table(title="Trash Tasker Schedule")
    table.add_column("Week", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Glass", justify="right", style="green")

    for i, row in df.iterrows():
        table.add_row(str(row["week"]), row["name"] or "N/A", "Yes" if row["glass"] else "No")

    console.print(table)


def send_next():
    if check_schedule_directory("schedule.csv", "directory.json") is False:
        logger.error("Some errors were found in the schedule or directory file")
        exit(1)
    td = datetime.datetime.now()
    _, week, _ = td.isocalendar()  #  year, week, day

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

            if cc_sms is True:
                send_sms(number_debug, message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="trash_tasker", description="Trash Tasker Console")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for 'send'
    send_parser = subparsers.add_parser("send", help="Send commands.")
    send_parser.add_argument("action", choices=["next"], help="Action to perform with send.")

    # Subparser for 'show'
    show_parser = subparsers.add_parser("show", help="Show information.")
    show_parser.add_argument("action", choices=["schedule"], help="Action to perform with show.")

    args = parser.parse_args()

    # Handle the commands
    if args.command == "send" and args.action == "next":
        send_next()
    elif args.command == "show" and args.action == "schedule":
        show_schedule()
    else:
        parser.print_help()
