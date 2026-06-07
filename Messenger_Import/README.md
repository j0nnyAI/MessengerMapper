# Facebook Messenger Export Instructions

Place your raw, unzipped Facebook Messenger export files directly into this directory before running the ingestion pipeline.

## How to Download Your Data from Meta via Messenger.com

1. **Access Messenger Settings**:
   - Go to [messenger.com](https://www.messenger.com/) and log into your account.
   - Click your **Profile Icon** located at the bottom left corner of the screen.
   - Click on **Privacy & safety** from the pop-up menu.

2. **Navigate to Message Store**:
   - Inside the Privacy & safety settings window, click on **End-to-end encrypted chats**.
   - Click on **Message store**.

3. **Request Your Information**:
   - Click on **Download message storage data**.

4. **Configure Timeframe & Content**:
   - **Timeframe**: Choose your target forensic timeframe (e.g., specific date windows or All Time).
   - **Content Selection**: Check the boxes next to **Messages** and **Media** (if you require media attachments for original aspect-ratio verification).

5. **Submit and Download**:
   - Click **Download**. 
   - *Note on Processing Time*: Depending on your selected media quality and target timeframe, you will have to wait either minutes (for low quality) or days (for higher-quality) for Meta to generate the data archive.
  
   Once you receive the notification that the file is ready, download the `.zip` archive, extract its contents, and place them directly into this folder.