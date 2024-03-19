# Jamf API
A collection of Jamf API things I've written or adapted. A blog post with additional context and details [Jamf Pro API - Mass Unmanage](https://www.rfgeeks.com/jens-blog/jamf-pro-api-mass-unmanage)

Since Jamf Pro 10.49 it is not possible to unmanage Macs by using Mass Action in the Jamf UI. Instead, the Python script Action-Jamf_Pro_API-UnmanageComputers.py utilizes the Jamf Pro API to perform an unmanage of a static group of Macs.

If you use this script to unmanage Macs, be aware that on the Macs it sets to be unmanaged it will also update the Last Inventory Date of that Mac to when the management status was set. This is a known issue with the Jamf Classic API as documented in this feature request from 2015 [JN-I-22670](https://ideas.jamf.com/ideas/JN-I-22670). Unfortunately, I could not find a Jamf Pro API method to set the management status of a Mac, so this script utilizes the Jamf Classic API to unmanage a Mac. The newer Jamf Pro API does not update the Last Inventory Date thankfully.

In addition, there are 2 other scripts Action-Jamf_Pro_API-Update_xEA-Jamf-Site.py and Action-Jamf_Pro_API_Update_Mobile_xEA-Jamf-Site.py that set an extension attribute for each Mac and Mobile Device with that device's Jamf site. As Jamf doesn't allow Jamf Site to be used as a search criteria for smart groups or saved searches by default, these scripts make site information available via an extension attribute. 

# Using these scripts
These scripts are expected to be run in a CI/CD environment like GitHub Actions, AWS, or CircleCI, etc. so certain secret values can be passed.
This requires the installation of the [JPS-API-Wrapper](https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper )

These scripts will allow you to do the following:
- Set Computer Extension Attribute Jamf Site 
- Set Mobile Device Extension Attribute Jamf Site 
- Unmanage a Static Group of Computers

If you don't want to use CI/CD you can just edit the scripts and hardcode or set prompts for requesting Jamf API credentials. 

## Setup
Clone this repository.

### Create or Update a Static Computer Group (Unmanage Computers Only)
These are the Macs that you want to be unmanaged. I use a tool, [MUT](https://github.com/jamf/mut) to add Macs to this static group.

### Setup Jamf API Roles and Clients
Use Jamf's documentation to configure [https://learn.jamf.com/bundle/jamf-pro-documentation-current/page/API_Roles_and_Clients.html](https://learn.jamf.com/bundle/jamf-pro-documentation-current/page/API_Roles_and_Clients.html)

- Read Computers
- Update Computers
- Read Computer Extension Attributes
- Update Computer Extension Attributes
- Read Mobile Devices
- Update Mobile Devices
- Read Mobile Device Extension Attributes
- Read Static Computer Groups
- Update User

Copy the client ID and client credentials for later use. You can separate out the API roles and clients if you wish. Create them as Text fields and Inventory Display to General.

### Create Computer Extension Attributes
In the Jamf Pro UI, create the following extension attributes. You can name them whatever you like.

#### Unmanage Computers
Also set the Data Type to Date (YYYY-MM-DD hh:mm:ss)

- xEA - Previous Last Inventory Date
  * The date the device actually last inventoried with Jamf
- xEA - Unmanaged Date
  * The date the API issued the unmanage command

#### Computer Extension Attribute Jamf Site 
- xEA - Jamf Site

#### Mobile Device Extension Attribute Jamf Site 
- xEA Mobile - Jamf Site

### Create GitHub Repository Secrets 
Use the steps in [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) to add secrets to your repository.

- JAMF_URL
  * Your Jamf Pro URL, e.g. https://jamfserver.jamfcloud.com
- JAMF_CLIENT_ID
  * The Jamf API Client ID
- JAMF_CLIENT_SECRET
  * The Jamf API Client Secret

### Update GitHub Action Workflow
Under .github/workflows edit the 3 YAML workflow files to match your environment's extension attribute names, IDs, static computer group name, and static group ID.

If you want this to run on a scheduled basis add something like below to the yml file. The cron settings below will have this run every day at 8:00 UTC.

    schedule:
        - cron:  0 8 * * *

### Update GitHub Action Workflow
When ready and you've tested extensively, click Actions in your repository. Then click on Unmanage Computers - Static Group from the left and then click Run workflow. Then click the green Run workflow button. Eventually, the run will show up under Actions, and you can click on it and watch its progress.

## Future Work
The current unmanage script does take some time to run, about 4 hours for ~700 Macs. Using some of the concurrent API functions, this time could be potentially reduced. 

The summary step in the workflow file that doesn’t appear to do anything.  My original concept was to have the output of the Python script go in the [GitHub Job Summary](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summar) that would be suitable for export or a way to see what the Unmanage workflow did at a glance. I couldn’t get the output from the underlying Python script to get into GitHub Actions. I'd love to hear from you if anyone has ideas on accomplishing this.

These scripts could be adapted to use the [Jamf Pro SDK for Python](https://github.com/macadmins/jamf-pro-sdk-python) instead. 