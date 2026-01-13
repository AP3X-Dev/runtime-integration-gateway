"""Generate RIG hero pack scaffolding."""

import os
from pathlib import Path

PACKS = {
    "twilio": {
        "description": "SMS, voice calls, and verification",
        "dependency": "twilio>=8.0.0",
        "auth_env": "TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN",
        "tools": [
            ("twilio.sms.send", "write", "Send an SMS message"),
            ("twilio.calls.create", "write", "Create a phone call"),
            ("twilio.calls.status", "read", "Get call status"),
            ("twilio.verify.start", "write", "Start verification"),
            ("twilio.verify.check", "write", "Check verification code"),
            ("twilio.messaging.services.list", "read", "List messaging services"),
        ]
    },
    "slack": {
        "description": "Slack messaging and collaboration",
        "dependency": "slack-sdk>=3.0.0",
        "auth_env": "SLACK_BOT_TOKEN",
        "tools": [
            ("slack.messages.post", "write", "Post a message to a channel"),
            ("slack.messages.update", "write", "Update a message"),
            ("slack.channels.list", "read", "List channels"),
            ("slack.users.lookupByEmail", "read", "Look up user by email"),
            ("slack.files.upload", "write", "Upload a file"),
            ("slack.reactions.add", "write", "Add a reaction"),
        ]
    },
    "sendgrid": {
        "description": "Email delivery and marketing",
        "dependency": "sendgrid>=6.0.0",
        "auth_env": "SENDGRID_API_KEY",
        "tools": [
            ("sendgrid.email.send", "write", "Send an email"),
            ("sendgrid.templates.list", "read", "List email templates"),
            ("sendgrid.templates.render", "read", "Render a template"),
            ("sendgrid.contacts.upsert", "write", "Upsert contacts"),
            ("sendgrid.suppressions.add", "write", "Add to suppression list"),
            ("sendgrid.stats.get", "read", "Get email statistics"),
        ]
    },
    "github": {
        "description": "GitHub repository management",
        "dependency": "PyGithub>=2.0.0",
        "auth_env": "GITHUB_TOKEN",
        "tools": [
            ("github.issues.create", "write", "Create an issue"),
            ("github.issues.comment", "write", "Comment on an issue"),
            ("github.pulls.create", "write", "Create a pull request"),
            ("github.pulls.list", "read", "List pull requests"),
            ("github.repos.create", "infra", "Create a repository"),
            ("github.actions.dispatchWorkflow", "infra", "Dispatch a workflow"),
        ]
    },
    "google": {
        "description": "Google Workspace (Sheets, Drive, Gmail)",
        "dependency": "google-api-python-client>=2.0.0,google-auth>=2.0.0",
        "auth_env": "GOOGLE_CREDENTIALS_JSON",
        "tools": [
            ("google.sheets.values.get", "read", "Get spreadsheet values"),
            ("google.sheets.values.update", "write", "Update spreadsheet values"),
            ("google.sheets.spreadsheets.create", "write", "Create a spreadsheet"),
            ("google.drive.files.create", "write", "Create a file in Drive"),
            ("google.drive.files.list", "read", "List files in Drive"),
            ("google.gmail.messages.send", "write", "Send an email via Gmail"),
        ]
    },
    "notion": {
        "description": "Notion workspace management",
        "dependency": "notion-client>=2.0.0",
        "auth_env": "NOTION_TOKEN",
        "tools": [
            ("notion.pages.create", "write", "Create a page"),
            ("notion.pages.update", "write", "Update a page"),
            ("notion.databases.query", "read", "Query a database"),
            ("notion.blocks.append", "write", "Append blocks to a page"),
            ("notion.search", "read", "Search Notion"),
            ("notion.users.list", "read", "List users"),
        ]
    },
    "airtable": {
        "description": "Airtable database management",
        "dependency": "pyairtable>=2.0.0",
        "auth_env": "AIRTABLE_API_KEY",
        "tools": [
            ("airtable.records.create", "write", "Create a record"),
            ("airtable.records.update", "write", "Update a record"),
            ("airtable.records.list", "read", "List records"),
            ("airtable.bases.list", "read", "List bases"),
            ("airtable.tables.list", "read", "List tables"),
            ("airtable.records.delete", "destructive", "Delete a record"),
        ]
    },
    "supabase": {
        "description": "Supabase backend services",
        "dependency": "supabase>=2.0.0",
        "auth_env": "SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY",
        "tools": [
            ("supabase.auth.createUser", "write", "Create a user"),
            ("supabase.auth.inviteUserByEmail", "write", "Invite user by email"),
            ("supabase.table.select", "read", "Select from table"),
            ("supabase.table.insert", "write", "Insert into table"),
            ("supabase.table.update", "write", "Update table rows"),
            ("supabase.storage.upload", "write", "Upload to storage"),
            ("supabase.storage.createSignedUrl", "read", "Create signed URL"),
        ]
    },
    "elevenlabs": {
        "description": "AI voice synthesis",
        "dependency": "elevenlabs>=1.0.0",
        "auth_env": "ELEVENLABS_API_KEY",
        "tools": [
            ("elevenlabs.voices.list", "read", "List available voices"),
            ("elevenlabs.textToSpeech.create", "write", "Generate speech from text"),
            ("elevenlabs.textToSpeech.stream", "write", "Stream speech from text"),
            ("elevenlabs.voice.clone", "write", "Clone a voice"),
            ("elevenlabs.audio.generateWithSettings", "write", "Generate with settings"),
            ("elevenlabs.projects.list", "read", "List projects"),
        ]
    },
}


def generate_pack(pack_id: str, config: dict, base_dir: Path):
    """Generate a pack structure."""
    pack_name = f"rig-pack-{pack_id}"
    pack_dir = base_dir / f"packages/{pack_name}"
    module_name = f"rig_pack_{pack_id}"
    module_dir = pack_dir / module_name
    tools_dir = module_dir / "tools"
    
    os.makedirs(tools_dir, exist_ok=True)
    
    # Generate pyproject.toml
    deps = config["dependency"].split(",")
    dep_list = ",\n  ".join([f'"{d.strip()}"' for d in deps])
    
    pyproject = f'''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{pack_name}"
version = "0.1.0"
description = "RIG Pack: {config['description']}"
readme = "README.md"
requires-python = ">=3.10"
license = {{text = "Apache-2.0"}}
authors = [{{name = "RIG Contributors"}}]
dependencies = [
  "rig-core>=0.1.0",
  {dep_list}
]

[project.entry-points."rig.packs"]
{pack_name} = "{module_name}.pack:PACK"

[tool.setuptools]
packages = ["{module_name}", "{module_name}.tools"]
'''
    
    with open(pack_dir / "pyproject.toml", "w") as f:
        f.write(pyproject)
    
    print(f"Generated {pack_name}")


if __name__ == "__main__":
    base = Path(__file__).parent.parent
    for pack_id, config in PACKS.items():
        generate_pack(pack_id, config, base)
    print("Done!")

