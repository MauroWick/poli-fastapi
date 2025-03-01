import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1dATbeFvLwCE3OymQAVwxalZNPUD8hyHDTd53RIwkgQc"
RANGE_NAME = "Sheet1!A:AX"

def get_values(spreadsheet_id, range_name):
    creds, _ = google.auth.default()
    try:
        service = build("sheets", "v4", credentials=creds)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        rows = result.get("values", [])
        print(f"{len(rows)} rows retrieved.")
        return result
    except HttpError as e:
        print(f"An error occurred: {e}")
        return e
