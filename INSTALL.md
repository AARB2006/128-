# Installing YT-MP3 on a Windows computer

This guide is for whoever sets YT-MP3 up on a family computer. It takes about 15 minutes the first time, mostly waiting.

YT-MP3 runs on the computer itself. **Setup** installs what's missing and builds the app. After that, the **YT-MP3** shortcut on the desktop starts the app and opens it in the browser. Everyone's songs and playlists are stored in Supabase, so they're the same on every computer each person signs in from.

---

## What you need

- Windows 10 or 11, with an internet connection.
- About 2 GB of free space (more while exporting large playlists).
- Permission to install programs. Windows may ask "Do you want to allow this app to make changes?" during Setup.

No passwords or keys are needed. The project's two public Supabase settings come with YT-MP3 (in `supabase-public.env`), and **no secret key is stored on family computers**: each computer can only ever act as the person signed in on it.

## Once per Supabase project (not per computer)

1. **Run the database upgrade.** In Supabase, open **SQL Editor**, paste the whole of `database/upgrade-01-no-secret-key.sql`, and run it. Running it again is harmless.
2. **Allow the app's address.** Go to **Authentication → URL Configuration → Redirect URLs** and add:

   ```text
   http://localhost:8000/**
   ```

   Without it, Google sign-in sends people to the wrong page after they choose their account.
3. **Limit who can sign in.** The repository is public, so anyone could find the project's address. Keep sign-in to your family. In **Google Cloud Console → Google Auth Platform → Audience**, keep the app in **Testing** and add each family member's Gmail address under **Test users**.
   - Alternatively, in Supabase, turn off **Authentication → Sign In / Providers → Allow new users to sign up** once everyone has signed in once. Turn it on briefly to add someone.

   Either way, a stranger who signs in only ever sees an empty library of their own. Limiting sign-in just keeps them out entirely.

## Install

1. **Download YT-MP3.** On the project's GitHub page, choose **Code → Download ZIP**.
2. **Unblock and extract it:**
   - Right-click the ZIP, choose **Properties**, tick **Unblock** (if it's there), and click **OK**.
   - Extract the ZIP to a folder you'll keep, for example `C:\Users\<name>\YT-MP3`.
   - Avoid folders synced by OneDrive (often **Desktop** and **Documents**). Setup creates thousands of small files that OneDrive would try to upload.
3. **Run Setup.** Double-click **Setup YT-MP3.bat**.
   - If Windows says "Windows protected your PC", click **More info → Run anyway**.
   - Setup checks for Python, Node.js and FFmpeg and installs any that are missing. Choose **Yes** if Windows asks for permission.
   - It asks nothing else. It reads the public settings from `supabase-public.env`. If that file is missing, it asks for the two public values (project URL and publishable key).
   - Wait for **Setup finished**, then close the window.

Setup only changes things inside the YT-MP3 folder, plus the programs above and a **YT-MP3** shortcut on the desktop.

## Using YT-MP3

1. Double-click **YT-MP3** on the desktop. A window opens, and then the app opens in the browser at `http://localhost:8000`.
2. Sign in with Google.
3. **Keep that window open** while using YT-MP3. Closing it stops the app.

Each start also updates yt-dlp, the part that reads YouTube, so imports keep working when YouTube changes.

## Updating to a new version

1. Download and extract the new version into a **new** folder.
2. Run **Setup YT-MP3.bat** in the new folder. It moves the desktop shortcut to the new folder.
3. Delete the old folder.

Songs, playlists and export history are stored in Supabase, so nothing is lost.

## Uninstalling

Delete the YT-MP3 folder and the desktop shortcut. Python, Node.js and FFmpeg can be removed under **Settings → Apps** if nothing else uses them. The person's library stays in their account and is there again if YT-MP3 is reinstalled.

## Troubleshooting

| What you see | What to do |
|---|---|
| "Windows protected your PC" | Click **More info → Run anyway**. Or unblock the ZIP before extracting (step 2). |
| "Extract the whole YT-MP3 ZIP to a folder first" | You opened the file inside the ZIP. Extract the ZIP, then run it from the folder. |
| Setup: "... was installed but this window cannot see it yet" | Close the window and run Setup again. |
| Setup: "winget ... isn't available" | Install **App Installer** from the Microsoft Store, then run Setup again. |
| Setup fails while installing packages | Check the internet connection and run Setup again. It continues where it can. |
| Start: "Another program is using port 8000" | Close that program, or restart the computer. |
| Start: "isn't set up on this computer yet" | Run **Setup YT-MP3.bat** first. |
| After choosing a Google account, you land on the wrong page or see a redirect error | Add `http://localhost:8000/**` to Supabase's Redirect URLs (see "Once per Supabase project" above). |
| Google says the app is in testing / access blocked | Add that person's Gmail address under **Test users** (see "Once per Supabase project", step 3). |
| Imports or exports fail with "Could not find the function public.start_import" | The database upgrade hasn't been run yet (see "Once per Supabase project", step 1). |
| Exports say the audio converter is missing | Run Setup again; it reinstalls FFmpeg. |
| Imports suddenly fail for every link | Restart YT-MP3 with internet on, so it can update yt-dlp. |

Setup keeps a log in `logs\setup.log` in the YT-MP3 folder. It's useful when asking for help.

## Security

- **No secret key on family computers.**
  - YT-MP3 works with each person's own Google sign-in. Starting an import or export gives that one job a key of its own, which stops working when the job ends.
  - A lost or hacked computer can therefore only reach the data of whoever was signed in on it, not everyone's.
  - If someone ever installed an older YT-MP3 that kept the secret key in `backend\.env`, running the new Setup removes it.
- **If a computer is lost:** that person can sign out of all devices from their Google account. Nothing else needs changing.
- **Only reachable from the computer itself.** YT-MP3 only listens on the computer itself (`127.0.0.1`), so other devices on the network can't reach it.
