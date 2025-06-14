# What's the ID?

Search for tracklists and split the DJ set into separate tracks.

## Architecture

This project consists of two components:

- **Backend Service** ([dj-set-downloader](https://github.com/jaki95/dj-set-downloader)): Handles downloading DJ sets and splitting them into individual tracks
- **Frontend UI** (this repository): Provides a Streamlit-based interface for searching for tracklists and managing the splitting process

## Setup

### 1. Start the Backend Service

First, clone and start the downloader/splitter backend service:

```bash
git clone https://github.com/jaki95/dj-set-downloader.git
cd dj-set-downloader && docker compose up
```

### 2. Run the Frontend UI

In a separate terminal, clone this repository and start the tracklist search interface:

```bash
git clone https://github.com/jaki95/whats-this-id.git
cd whats-this-id
uv run streamlit run src/whats_this_id/frontend/app.py
```

The frontend will connect to the backend service to process your DJ sets and split them into individual tracks.


