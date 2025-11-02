# What's the ID?

Search for tracklists and split the DJ set into separate tracks.

## Architecture

This project consists of two components:

- **Backend Service** ([dj-set-downloader](https://github.com/jaki95/dj-set-downloader)): Handles downloading DJ sets and splitting them into individual tracks
- **Frontend UI** (this repository): Provides a Streamlit-based interface for searching for tracklists and managing the splitting process

## Setup

### 0. Configure OpenAI API (Optional)

If you want to use the AI metadata extraction feature, create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then add your OpenAI API key:

```bash
OPENAI_API_KEY=your_key_here
```

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
make run
```

The frontend will connect to the backend service to process your DJ sets and split them into individual tracks.

## Features

- **Tracklist Search**: Search for DJ set tracklists and select the one you want to process
- **AI Metadata Extraction**: Use OpenAI GPT-4o-mini to automatically extract artist names and years from DJ set titles
- **Track Splitting**: Split DJ sets into individual tracks based on tracklist timings
- **Download**: Download individual tracks or the full set as a ZIP file


