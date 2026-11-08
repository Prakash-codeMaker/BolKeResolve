# Update an existing BolKeResolve install without losing cases

**Important:** the ZIP intentionally does not include local cases, uploaded evidence, or your `.env` secrets.

1. Stop the running app in its PowerShell/terminal window with `Ctrl+C`.
2. Make a backup copy of the old project's `.env` file and `runtime` folder. The `runtime` folder contains the local SQLite database and evidence files.
3. Extract `BolKeResolve_Multilingual_Case_Workspace.zip` into a new folder, or carefully merge the updated files into the existing project folder.
4. Restore the old `.env` file into the new project folder. Do not paste your API key into source code or share it publicly.
5. Copy the old `runtime` folder into the new project folder so the new version sees the same local database and evidence. If the new folder already has a runtime directory, merge the old files into it and keep a backup first.
6. Run `run_windows.bat` and open `http://127.0.0.1:8000`.
7. Open your existing Zomato case. Click **Refresh plan ↻**. The saved description should be reclassified as **Refund not received**, and the page will show the compact Next steps / Evidence / Message / Activity workspace.

If you are not sure where the old database is, do not delete the old project directory. Keep it as a backup and ask for help identifying the `runtime` folder before replacing anything.
