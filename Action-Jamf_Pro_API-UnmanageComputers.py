#!/usr/bin/env python3

"""
In Jamf Pro version 10.49 and higher, Jamf has removed the ability to mass edit management account settings
from a saved search results page via mass actions. 

This script will take the JSS ID from a static group, grab the ID of each device and store it in a Python list. 
Then it will iterate through that list and send Classic API commands to remove the management account.

You must provide the ID of the advanced computer search, "Static_Group_ID"

This is expected to be run in a CI environment (GitHub Actions) so certain secret values can be passed from the CI
This requires the installation of the JPS-API-Wrapper: https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper

Additional Resources
https://derflounder.wordpress.com/2023/08/15/updating-management-status-in-jamf-pro-computer-inventory-records-on-jamf-pro-10-49-0-and-later/
https://gist.github.com/t-lark/0c1dc014a22035e61bd073fa48dd82f9 

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
JSS_URL = os.environ.get("JAMF_URL")
CLIENT_ID = os.environ.get("JAMF_CLIENT_ID")
CLIENT_SECRET = os.environ.get("JAMF_CLIENT_SECRET")
# Specify our unique Jamf Pro port, default is 443
# port="8443"

# Set the Extension Attribute Names and IDs
xEA_Unmanage_Date_name = os.environ.get("JAMF_xEA_NAME_1")
xEA_Unmanage_Date_id = os.environ.get("JAMF_xEA_ID_1")
xEA_Previous_Date_name = os.environ.get("JAMF_xEA_NAME_2")
xEA_Previous_Date_id = os.environ.get("JAMF_xEA_ID_2")

# Set the Static Group ID we're going to be updating
Static_Group_ID = os.environ.get("JAMF_STATIC_GROUP_ID")

def main():
    classic = Classic(JSS_URL, CLIENT_ID, CLIENT_SECRET, client=True)

    # Retrieves all the computer ids and computer names
    all_computers = classic.get_computer_group(id=Static_Group_ID)["computer_group"]["computers"]
    # For every computer ID found do the following
    for computer in all_computers:
        # Get the JSS ID and Computer Name
        device_id = computer["id"]
        # Get the computer name
        computer_name = computer["name"]
        # Get details from the General subset about the Computer ID
        current = classic.get_computer(id=device_id,subsets=["General"])
        # Get the site name
        site_name = current["computer"]["general"]["site"]["name"]
        # Get the management status
        managed_status = current["computer"]["general"]["remote_management"]["managed"]

        # Get the previous last inventory date and the current date and time
        last_inventory_date = current["computer"]["general"]["report_date"]
        current_datetime = datetime.now(timezone.utc)
        # Format the current date and time to match what Jamf reports for last inventory date
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Only update the computer record if the Mac is currently managed, saving on API calls
        if managed_status == True:
            # Format the XML data to update the computer record: Unmanage, Set xEA - Unmananged Date, Set xEA - Previous Inventory Date
            try:
                # Set the Managed by to blank
                print(f"Unmanaged - JSS ID: {device_id}, Computer Name: {computer_name}, Site Name: {site_name}")
                payload = f'<computer><general><remote_management><managed>false</managed></remote_management></general></computer>'
                classic.update_computer(id=device_id, data=payload)

                # Set the value for xEA - Unmanaged Date
                payload_xEA = f'<computer><extension_attributes><extension_attribute><id>{xEA_Unmanage_Date_id}</id><value>{formatted_datetime}</value></extension_attribute></extension_attributes></computer>'
                classic.update_computer(id=device_id, data=payload_xEA)

                # Set the value for xEA - Previous Last Inventory Date
                print(f"JSS ID: {device_id}, Computer Name: {computer_name}, Unmanaged Date: {formatted_datetime}, Previous Inventory Date: {last_inventory_date}")
                payload_xEA = f'<computer><extension_attributes><extension_attribute><id>{xEA_Previous_Date_id}</id><value>{last_inventory_date}</value></extension_attribute></extension_attributes></computer>'
                classic.update_computer(id=device_id, data=payload_xEA)

            # Jamf Pro API may throw an exception or error, try to handle it here
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for ID: {device_id}")
                print(err.args[0])

if __name__ == '__main__':
    main()
