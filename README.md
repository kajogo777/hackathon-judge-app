# Hackathon Judge App

A Streamlit web application for judging hackathon pitches. Designed to be accessible through mobile web browsers with persistent data storage.

## Features

- Judge selection: Each judge can select their name before scoring teams
- Team scoring: Judges can score teams based on configurable criteria
- Score persistence: All scores are saved to a local JSON file
- Mobile-friendly design: Optimized for use on mobile devices
- Configurable through YAML: Easy to adjust teams, judges, and judging criteria
- Custom branding: Add your event logo and title for personalized experience

## Setup Instructions

1. Make sure you have Python 3.7+ installed
2. Clone this repository
3. Install uv if you don't have it already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

4. Create a virtual environment and install the required dependencies with uv:

```bash
uv venv
uv pip install streamlit==1.31.0 pyyaml==6.0.1 pillow==10.0.0
```

5. Configure the app by editing `config.yaml`:
   - Set your event title and logo (optional)
   - Add judge names
   - Set team names
   - Configure prize categories and their criteria

## Running the App

Run the Streamlit app using uv:

```bash
uv run streamlit run app.py
```

The app will be available at `http://localhost:8501`

For access from other devices on the same network, find your computer's IP address and use:

```bash
uv run streamlit run app.py -- --server.address 0.0.0.0
```

This will make the app accessible to all devices on your local network via `http://your-ip-address:8501`

## Customizing the App

Edit the `config.yaml` file to customize:

- Event information:
  - `event.title`: The name of your hackathon or event
  - `event.logo_path`: Path to your event logo (relative to app.py)
- List of judges' names
- List of participating teams
- Prize categories and judging criteria
- Maximum score for each criterion

## Environment Variables

The app supports the following environment variables:

- `APP_PASSCODE`: The passcode that users must enter to access the app (default: "hackathon2025")

Example of setting environment variables:

```bash
# Linux/Mac
export APP_PASSCODE="your_secure_passcode"
uv run streamlit run app.py

# Windows
set APP_PASSCODE=your_secure_passcode
uv run streamlit run app.py
```

## Data Storage

All judging data is stored in a `scores.json` file in the same directory as the app. The file is created automatically when the first scores are saved.

## Vibe Deploy

```bash
stakpak agent run -i -a norbert:v1 "deploy this streamlit app on AWS, with TLS, and using the route53 subdomain hackjudge.stakpak.dev"
```

## License

MIT
