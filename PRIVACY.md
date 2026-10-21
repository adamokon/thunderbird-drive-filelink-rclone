# Privacy and data handling

Drive Filelink via rclone is a Thunderbird add-on and a local companion program.
The project's maintainer does not operate an upload server, receive file contents,
collect analytics, or receive users' Google passwords or OAuth tokens through this software.

## Data flow

When you explicitly convert an attachment to Filelink, its name and contents pass
from Thunderbird to a local Native Messaging helper. The helper temporarily stores
a copy on your computer and asks your locally installed rclone to upload it directly
to your Google Drive. Google receives the file, its name and API request metadata.
The returned sharing URL is inserted into your email, which is processed by your
email provider and the recipient's email provider in the usual way.

The app requests only the Google OAuth scope `drive.file`. It can manage files it
creates and files you explicitly make available to that app. It does not request
full access to every file on your Drive, Gmail API access, or your Google password.

## Local credentials and storage

rclone stores your OAuth client information and tokens in a dedicated configuration
file outside the source repository. The add-on does not receive those credentials.
The configuration is protected with operating-system file permissions; it is not
an encrypted hardware-backed vault. Other processes running as your local user may
be able to read it. The extension stores only local account enablement settings.

The temporary file copy is removed on normal completion and handled termination.
A forced process kill or system crash can leave a temporary copy on the computer.
Uploaded files remain in Drive until you remove them. Interrupted uploads may also
leave uploaded files or sharing permissions in Drive.

## Sharing and deletion

Enabling Filelink and selecting an upload creates a public read-only link for that
individual file. Anyone who possesses that URL can read the file and pass the link
on. The software does not make the containing folders public. Links have no password
and no automatic expiration in this version.

To revoke a link, use Google Drive's sharing settings and change General access to
Restricted. Review any other permissions. Revocation cannot remove copies already
downloaded by recipients. Removing a mail attachment or uninstalling the add-on
does not delete files from Drive or revoke existing links.

You can revoke the application's Google authorization through your Google Account
connections page. Uninstalling the helper preserves the local rclone configuration
so it is not accidentally lost; you can remove that dedicated configuration yourself.

## Third parties and support

Google and your email provider process the data under their respective policies.
GitHub hosts this project's source and documentation; no real OAuth credentials or
private test artifacts belong in that repository. Do not post credentials, private
files or real sharing URLs in issues. See [SECURITY.md](SECURITY.md) for security reports.

This policy describes the software as provided in this repository. It does not
cover modifications made by other parties or unrelated browser extensions/services.
