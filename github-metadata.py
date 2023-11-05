import requests
import json
import yaml
import base64
import os

# GitHub API base URL
BASE_URL = "https://api.github.com"

# Your GitHub username and personal access token 
USERNAME = "ashokbubli"
TOKEN = os.environ.get("PAT")


# Function to get the list of all repositories for your GitHub account (including private repositories)
def get_repositories(username, token):
    repositories = []
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}/user/repos?page={page}&per_page=100",  # Increase per_page if you have more repositories
            headers={"Authorization": f"token {token}"}
        )

        if response.status_code == 200:
            repos = response.json()
            if not repos:
                break

            repositories.extend(repos)
            page += 1
        else:
            print(f"Error fetching repositories. Check your username and token.")
            break

    return repositories

# Function to parse YAML content with or without indentation
def parse_yaml_content(content_data):
    try:
        content_text = base64.b64decode(content_data).decode("utf-8")
        metadata = yaml.safe_load(content_text)

        if metadata is None:
            metadata = {}  # Handle empty YAML
    except Exception as e:
        metadata = {}  # Treat YAML parsing errors as blank fields

    return metadata

# Get the current list of repositories from GitHub
current_repositories = get_repositories(USERNAME, TOKEN)

# Create a copy of the existing metadata list
existing_metadata_list = []

# Update or add metadata for each current repository
for repo in current_repositories:
    repo_name = repo['name']
    repo_url = repo['html_url']

    # Check if the .abd folder exists in the repository
    response_abd = requests.get(f"{BASE_URL}/repos/{USERNAME}/{repo_name}/contents/.abd", headers={"Authorization": f"token {TOKEN}"})
    
    if response_abd.status_code != 200:
        # The .abd folder does not exist, set "Application" field and other fields accordingly
        metadata_dict = {
            "Repository": repo_name,
            "Application": "Repository metadata not available",
            "IT Owner": "",
            "Key Expert": "",
            "Hosted Environment": "",
            "Accessibility": "",
            "Business Service Name": "",
        }
        existing_metadata_list.append(metadata_dict)
        continue

    # Fetch the contents of app.yaml/app.yml from the repository
    response_yaml = requests.get(f"{BASE_URL}/repos/{USERNAME}/{repo_name}/contents/.abd/app.yaml", headers={"Authorization": f"token {TOKEN}"})
    response_yml = requests.get(f"{BASE_URL}/repos/{USERNAME}/{repo_name}/contents/.abd/app.yml", headers={"Authorization": f"token {TOKEN}"})

    response = response_yaml if response_yaml.status_code == 200 else response_yml

    if response.status_code == 200:
        content = response.json()
        content_data = content.get("content", "")

        # Parse YAML content with exception handling
        metadata = parse_yaml_content(content_data)

        # Define the structure of the metadata dictionary
        metadata_dict = {
            "Repository": repo_name,
            "Application": "",
            "IT Owner": "",
            "Key Expert": "",
            "Hosted Environment": "",
            "Accessibility": "",
            "Business Service Name": "",
        }

        if 'application' in metadata:
            metadata_dict["Application"] = metadata['application']

        if 'contacts' in metadata and isinstance(metadata['contacts'], dict):
            contacts = metadata['contacts']
            metadata_dict["IT Owner"] = contacts.get('it-owner', "")
            metadata_dict["Key Expert"] = ", ".join(contacts.get('key-expert', []))
            metadata_dict["Hosted Environment"] = contacts.get('hosted-env', "")
            metadata_dict["Accessibility"] = contacts.get('accessibility', "")

        if 'servicenow' in metadata and isinstance(metadata['servicenow'], dict):
            servicenow = metadata['servicenow']
            metadata_dict["Business Service Name"] = servicenow.get('business-service-name', "")

        # Replace None values with blank strings
        for key, value in metadata_dict.items():
            if value is None:
                metadata_dict[key] = ""

        # Check if the metadata is empty and set a message in the "Application" field if it doesn't match the expected structure
        if not any(metadata_dict.values()):
            metadata_dict["Application"] = "Repository metadata not available"

        existing_metadata_list.append(metadata_dict)

# Write the updated metadata list to a JSON file
with open("repository_metadata.json", "w") as json_file:
    json.dump(existing_metadata_list, json_file, indent=4, ensure_ascii=False, default=str)

print("JSON report generated successfully.")

