#!/usr/bin/env python3

"""
This script will take the JSS ID from a static group of Mobile Devices, grab the ID of each device and store it in a Python list. 
Then it will iterate through that list and send Classic API commands to set the Managed: field to "Unmanaged".

If you want to issue a command to have Mobile Devices unmanage themselves, see Action-Jamf_Pro_API-CommandUnmanageMobileDevices.py

You must provide the ID of the advanced mobile device search, "Static_Group_ID"

This is expected to be run in a CI environment (GitHub Actions) so certain secret values can be passed from the CI
This requires the installation of the JPS-API-Wrapper: https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper

Version 0.6
Jennifer Johnson 
04/05/24
"""

from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro
from datetime import datetime, timezone
import logging
import os
import requests

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

# file log handler
file = logging.FileHandler("output.log",mode='w')
file.setFormatter(logformat)

# console log handler
console = logging.StreamHandler()
console.setFormatter(logformat)

# add handlers
logger.addHandler(file)
logger.addHandler(console)

# Get the Jamf URL and crendentials
JSS_URL = os.environ.get("JSS_URL")
CLIENT_ID = os.environ.get("JSS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("JSS_CLIENT_SECRET")
# Specify our unique Jamf Pro port, default is 443
port="8443"

# Set the Extension Attribute Names and IDs
xEA_Unmanage_Date_name = os.environ.get("JSS_MOBILE_xEA_NAME")
xEA_Unmanage_Date_id = os.environ.get("JSS_MOBILE_xEA_ID")

# Set the Static Group ID we're going to be updating
Static_Group_ID = os.environ.get("JSS_MOBILE_STATIC_GROUP_ID")

def main():
    classic = Classic(JSS_URL, CLIENT_ID, CLIENT_SECRET, client=True)

    # Retrieves all the mobile device ids and mobile device names from the static group
    all_devices = classic.get_mobile_device_group(id=Static_Group_ID)["mobile_device_group"]["mobile_devices"]
    # For every mobile device ID found do the following
    for device in all_devices:
        # Get the JSS ID and mobile device Name
        device_id = device["id"]
        # Get the mobile device name
        device_name = device["name"]
        # Get details from the General subset about the mobile device ID
        current = classic.get_mobile_device(id=device_id,subsets=["General"])
        # Get the site name
        site_name = current["mobile_device"]["general"]["site"]["name"]
        # Get the management status
        managed_status = current["mobile_device"]["general"]["managed"]

        # Get the previous last inventory date and the current date and time
        last_inventory_date = current["mobile_device"]["general"]["last_inventory_update"]
        current_datetime = datetime.now(timezone.utc)
        # Format the current date and time to match what Jamf reports for last inventory date
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Only update the mobile device record if the Mac is currently managed, saving on API calls
        if managed_status == True:
            # Format the XML data to update the mobile device record: Unmanage, Set xEA - Unmananged Date, Set xEA - Previous Inventory Date
            try:
                # Set the Managed by to blank
                print(f"Unmanaged JSS ID: {device_id}, Mobile Device Name: {device_name}, Site Name: {site_name}, Previous Inventory Date: {last_inventory_date}, {xEA_Unmanage_Date_name}: {formatted_datetime}")
                payload = f'<mobile_device><general><managed>false</managed></general></mobile_device>'
                classic.update_mobile_device(id=device_id, data=payload)

                # Set the value for xEA - Unmanaged Date
                payload_xEA = f'<mobile_device><extension_attributes><extension_attribute><id>{xEA_Unmanage_Date_id}</id><value>{formatted_datetime}</value></extension_attribute></extension_attributes></mobile_device>'
                classic.update_mobile_device(id=device_id, data=payload_xEA)

            # Jamf Pro API may throw an exception or error, try to handle it here
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for ID: {device_id}")
                print(err.args[0])

if __name__ == '__main__':
    main()