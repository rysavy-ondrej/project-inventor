#!/bin/bash
echo "Uploading data files..."
# Config
REPO_OWNER="rysavy-ondrej"
REPO_NAME="inventor-analysis"
SOURCE_FOLDER="/root/project-inventor/testbed/out"
LOG_FILE="/var/log/github_upload.log"

# Check if token is set, GITHUB_TOKEN should be set as environment variable
if [ -z "$GITHUB_TOKEN" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: GITHUB_TOKEN environment variable is not set" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: GITHUB_TOKEN environment variable is not set"
  exit 1
fi

# Get yesterday's date in format YYYY-MM-DD
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting upload for files from $YESTERDAY" # >> "$LOG_FILE"

# Loop through files created yesterday
find "$SOURCE_FOLDER" -type f -name "*${YESTERDAY}.json" | while read -r LOCAL_FILE_PATH; do
  FILENAME=$(basename "$LOCAL_FILE_PATH")
  SERVICE_NAME=$(echo "$FILENAME" | cut -d'.' -f2-3)
  FILE_PATH_IN_REPO="data/$SERVICE_NAME/$FILENAME"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing $FILENAME for upload to $FILE_PATH_IN_REPO" # >> "$LOG_FILE"

  # Read file content and base64 encode it
  if ! CONTENT=$(base64 -w 0 "$LOCAL_FILE_PATH" 2>>"$LOG_FILE"); then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to encode $FILENAME" # >> "$LOG_FILE"
    continue
  fi

  # Create temporary payload file
  PAYLOAD_FILE=$(mktemp)
  cat > "$PAYLOAD_FILE" <<EOF
{
  "message": "Add file: $FILENAME",
  "content": "$CONTENT",
  "branch": "main"
}
EOF

  echo "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/contents/$FILE_PATH_IN_REPO"

  # Upload to GitHub
  RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/upload_response.json -X PUT \
       -H "Accept: application/vnd.github+json" \
       -H "Authorization: Bearer $GITHUB_TOKEN" \
       -H "Content-Type: application/json" \
       --data @"$PAYLOAD_FILE" \
       "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/contents/$FILE_PATH_IN_REPO")

  if [[ "$RESPONSE" == "201" || "$RESPONSE" == "200" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Successfully uploaded $FILENAME" #>> "$LOG_FILE"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to upload $FILENAME (HTTP $RESPONSE)" #>> "$LOG_FILE"
    cat /tmp/upload_response.json >> "$LOG_FILE"
  fi

  # Cleanup
  rm -f "$PAYLOAD_FILE"

done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upload process completed" #>> "$LOG_FILE"
