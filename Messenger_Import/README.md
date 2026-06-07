# Facebook Messenger Export Instructions

Place your raw, unzipped Facebook Messenger export files directly into this directory before running the ingestion pipeline.

## How to Download Your Data from Meta via Messenger.com

1. **Access Messenger Settings**:
   - Go to [messenger.com](https://www.messenger.com/) and log into your account.
   - Click your **Profile Icon** located at the bottom left corner of the screen.
   - Click on **Preferences** from the pop-up menu.

2. **Navigate to Accounts Center**:
   - Inside the Preferences window, click on **Account settings**. This will redirect you to the Meta Accounts Center.

3. **Request Your Information**:
   - In the left-hand menu, select **Your information and permissions**.
   - Click on **Download your information**.
   - Select **Download or transfer information**.

4. **Select Profiles**:
   - Choose the specific Facebook profile associated with the target chat logs.

5. **Choose Types of Information**:
   - Choose **Specific types of information** to avoid downloading an unnecessary global account archive.
   - Scroll down and check the box next to **Messages**.

6. **Configure Media & Format Options (Critical)**:
   - **Destination**: Select **Download to device**.
   - **Date Range**: Set your target forensic timeframe (e.g., specific date windows or All Time).
   - **Format**: Change this from HTML to **JSON** (The extraction engine requires structured JSON data).
   - **Media Quality**: Set to **High** if you require original aspect-ratio verification for embedded image or video attachments.

7. **Submit Request**:
   - Click **Create files**. Meta will generate the data archive. Once you receive the notification that the file is ready, download the `.zip` archive, extract its contents, and place them directly into this folder.