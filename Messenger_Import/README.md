# Facebook Messenger Export Instructions

Place your raw, unzipped Facebook Messenger export files directly into this directory before running the ingestion pipeline.

## How to Download Your Data from Meta

1. **Navigate to Accounts Center**:
   - Go to [facebook.com/your_information](https://www.facebook.com/your_information) or access **Accounts Center** via Instagram/Facebook settings.
2. **Request Your Information**:
   - Click on **Download your information**.
   - Select **Download or transfer information**.
3. **Select Profiles**:
   - Choose the specific Facebook profile associated with the chat logs.
4. **Choose Types of Information**:
   - Select **Specific types of information** rather than a complete copy.
   - Scroll down and check **Messages**.
5. **Configure Media & Format Options (Critical)**:
   - **Destination**: Download to device.
   - **Date Range**: Select your target forensic timeframe (e.g., specific dates or All Time).
   - **Format**: Change this from HTML to **JSON** (The `core/parse_calls.py` engine requires structural JSON).
   - **Media Quality**: Select **High** if you require original aspect-ratio verification for image/video attachments.
6. **Submit Request**:
   - Click **Create files**. Meta will process the archive. Once notified (typically minutes to hours depending on size), download the zip file and extract its contents directly into this folder.
