# trash-tasker
Send automatic SMS to my neighbours to remind them to take out trash using OVH API.

## Prerequisites

- Python 3.x
- Python `virtualenv` package
- OVH API credentials

## Setup Instructions

### 1. Setup config files

Create ovh-get.conf and ovh.conf files with your OVH API credentials.

The `schedule.csv` file contains the schedule for each week.
It has three columns: `week`, `name`, and `glass`.
The `name` column should contain the key from `directory.json` for the person responsible for taking out
the trash that week. The `glass` column is optional and can be used to indicate if glass recycling is
also required that week.
Note, you don't have to fill the whole year if some part of the schedule is not defined yet you can leave
blank name when required.

The `directory.json` file contains the contact information for each person.
Each key should match the `name` column in `schedule.csv`.
Each entry should have a `name` list and a `phone` list.
The `name` list contains the names of the people, and the `phone` list contains their corresponding phone numbers.


### 2. Clone the Repository

```sh
git clone <repository-url> /opt/trash-tasker
cd /opt/trash-tasker
chmod +x trash-tasker.sh
```

Setup virtualenv and install Python dependencies

```sh
python3 -m virtualenv venv
source ./venv/bin/activate
pip install ovh
pip install pandas
```

### 3. Set Up the Service

Copy the service and timer files to the systemd directory:

```sh
sudo cp trash-tasker.service /etc/systemd/system/
sudo cp trash-tasker.timer /etc/systemd/system/
```

Enable and Start the Timer

```sh
sudo systemctl enable trash-tasker.timer
sudo systemctl start trash-tasker.timer
```

You can check the status of the timer and service using:

```sh
sudo systemctl status trash-tasker.timer
sudo systemctl status trash-tasker.service
```


## Logging

Logs are written to `/var/log/trash-tasker.log`. You can view the logs using:

```sh
tail -f /var/log/trash-tasker.log
```