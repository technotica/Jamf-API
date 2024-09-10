# Jamf API
A collection of Jamf API things I've written or adapted. A blog post with additional context and details, specifically about doing unmanages of Macs: [Jamf Pro API - Mass Unmanage](https://www.rfgeeks.com/jens-blog/jamf-pro-api-mass-unmanage)

## Unmanage Computers
Since Jamf Pro 10.49 it is not possible to unmanage Macs by using Mass Action in the Jamf UI. Instead, the Python script [Action-Jamf_Pro_API-UnmanageComputers.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-UnmanageComputers.py) utilizes the Jamf Pro API to perform an unmanage of a static group of Macs.

If you use this script to unmanage Macs, be aware that on the Macs it sets to be unmanaged it will also update the Last Inventory Date of that Mac to when the management status was set. This is a known issue with the Jamf Classic API as documented in this feature request from 2015 [JN-I-22670](https://ideas.jamf.com/ideas/JN-I-22670). Unfortunately, I could not find a Jamf Pro API method to set the management status of a Mac, so this script utilizes the Jamf Classic API to unmanage a Mac.

## Unmanage Mobile Devices
For Mobile Devices, you can use [Action-Jamf_Pro_API-UnmanageMobileDevices.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-UnmanageMobileDevices.py) or [Action-Jamf_Pro_API-CommandUnmanageMobileDevices.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-CommandUnmanageMobileDevices.py) 

[Action-Jamf_Pro_API-UnmanageMobileDevices.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-UnmanageMobileDevices.py) behaves the same as Unmanage Computers, where it just sets the Managed field for the Mobile Device to Unmanaged.  

[Action-Jamf_Pro_API-CommandUnmanageMobileDevices.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-CommandUnmanageMobileDevices.py) will send an MDM Command to have the Mobile Devices unmanage themselves. Once the Mobile Device gets this command, it will remove the MDM Profile, device certificate, Self Service, managed apps, and any configuration profiles from the Mobile Device and then report its status to Jamf as Unmanaged. This has the benefit of removing all the Jamf and MDM bits from the device. However, if the device never turns on or can't receive that MDM command, it will stay managed. 

## Extension Attribute - Jamf Site (Computers and Mobile Devices)
[Action-Jamf_Pro_API-Update_xEA-Jamf-Site.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-Update_xEA-Jamf-Site.py) and [Action-Jamf_Pro_API_Update_Mobile_xEA-Jamf-Site.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API_Update_Mobile_xEA-Jamf-Site.py), set an extension attribute for each Mac and Mobile Device with that device's Jamf site. As Jamf doesn't allow Jamf Site to be used as a search criteria for smart groups or saved searches by default, these scripts make site information available via an extension attribute. 

## Extension Attribute - macOS Latest Supported
The script Action-Jamf_Pro_API-Update_xEA-macOS_Latest_Supported.py, sets an extension attribute for each Mac in Jamf with its latest supported macOS. It utilizes regex to compare the Mac's Model Identifier and spits out the latest supported macOS for that Mac. The regex has been helpfully compiled and updated by [TalkingMoose](https://gist.github.com/talkingmoose).

- [macOS 15 Sequoia](https://gist.github.com/talkingmoose/da84016836b29f125dad78414d0a4413)
- [macOS 14 Sonoma](https://gist.github.com/talkingmoose/1b852e5d4fc8e76b4400ca2e4b3f3ad0) 
- [macOS 13 Ventura](https://gist.github.com/talkingmoose/3100dab934baa13a799ba29be62ca357)
- [macOS 12 Monterey](https://gist.github.com/talkingmoose/74731895981b14da4ce1d524eeebdf1d)
- [macOS 11 Big Sur](https://gist.github.com/talkingmoose/794f7647e7a29d6ef74f8b9233dd44bb)

# Using These Scripts
These scripts are expected to be run in a CI/CD environment like GitHub Actions, AWS, or CircleCI, etc. so certain secret values can be passed.
This requires the installation of the [JPS-API-Wrapper](https://gitlab.com/cvtc/appleatcvtc/jps-api-wrapper)

These scripts will allow you to do the following:
- Set Computer Extension Attribute Jamf Site 
- Set Mobile Device Extension Attribute Jamf Site 
- Set Computer Extension Attribute macOS Latest Supported
- Unmanage a Static Group of Computers
- Unmanage a Static Group of Mobile Devices
- Send a Unmanage Device MDM command to a static group of Mobile Devices

If you don't want to use CI/CD you can just edit the scripts and hardcode or set prompts for requesting Jamf API credentials. 

## Instructions for using Unmanage Computers
Below are steps you can use to use [Action-Jamf_Pro_API-UnmanageComputers.py](https://github.com/technotica/Jamf-API/blob/main/Action-Jamf_Pro_API-UnmanageComputers.py) and related YAML workflow in GitHub Actions. If you want to use any of the other scripts or workflows, just adapt these steps to fit.

### Create or Update a Static Computer Group (Unmanage Computers Only)
These are the Macs that you want to be unmanaged. I use a tool, [MUT](https://github.com/jamf/mut) to add Macs to this static group.

### Setup Jamf API Roles and Clients
Use Jamf's documentation to configure [https://learn.jamf.com/bundle/jamf-pro-documentation-current/page/API_Roles_and_Clients.html](https://learn.jamf.com/bundle/jamf-pro-documentation-current/page/API_Roles_and_Clients.html)

- Read Computers
- Update Computers
- Read Computer Extension Attributes
- Update Computer Extension Attributes
- Read Static Computer Groups
- Update User

Copy the client ID and client credentials for later use. You can separate out the API roles and clients if you wish.

### Create Computer Extension Attributes
In the Jamf Pro UI, create the following extension attributes. You can name them whatever you like. Be sure to set them as Text fields and Inventory Display to General.

#### Unmanage Computers
Also set the Data Type to Date (YYYY-MM-DD hh:mm:ss)

- xEA - Previous Last Inventory Date
  * The date the device actually last inventoried with Jamf
- xEA - Unmanaged Date
  * The date the API issued the unmanage command

#### Computer Extension Attribute Jamf Site 
- xEA - Jamf Site

### Create GitHub Repository Secrets 
Use the steps in [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) to add secrets to your repository.

- JAMF_URL
  * Your Jamf Pro URL, e.g. https://jamfserver.jamfcloud.com
- JAMF_CLIENT_ID
  * The Jamf API Client ID
- JAMF_CLIENT_SECRET
  * The Jamf API Client Secret

### Update GitHub Action Workflow
Under .github/workflows edit the YAML workflow file [Computers-Unmanage.yml](https://github.com/technotica/Jamf-API/blob/main/.github/workflows/Computers-Unmanage.yml) to match your environment's extension attribute names, IDs, static computer group name, and static group ID.

If you want this to run on a scheduled basis add something like below to the yml file. The cron settings below will have this run every day at 8:00 UTC.

    schedule:
        - cron:  0 8 * * *

### Update GitHub Action Workflow
When ready and you've tested extensively, click Actions in your repository. Then click on Unmanage Computers - Static Group from the left and then click Run workflow. Then click the green Run workflow button. Eventually, the run will show up under Actions, and you can click on it and watch its progress.

# Future Work
The current unmanage script does take some time to run, about 4 hours for ~700 Macs. Using some of the concurrent API functions, this time could be potentially reduced. 

The summary step in the workflow file that doesn’t appear to do anything.  My original concept was to have the output of the Python script go in the [GitHub Job Summary](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summar) that would be suitable for export or a way to see what the Unmanage workflow did at a glance. I couldn’t get the output from the underlying Python script to get into GitHub Actions. I'd love to hear from you if anyone has ideas on accomplishing this.

These scripts could be adapted to use the [Jamf Pro SDK for Python](https://github.com/macadmins/jamf-pro-sdk-python) instead. 