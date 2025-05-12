import streamlit as st
import yaml
import json
import os
import pandas as pd
from datetime import datetime
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Hackathon Judge App",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for logo centering and styling
st.markdown(
    """
<style>
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 0.5rem;
    }
    .logo-container img {
        max-width: 100%;
        height: auto;
    }
    .event-title {
        text-align: center;
        margin-top: 0;
        margin-bottom: 1rem;
    }
    .winner {
        font-weight: bold;
        color: #FFD700;
    }
    .runner-up {
        font-weight: bold;
        color: #C0C0C0;
    }
    .third-place {
        font-weight: bold;
        color: #CD7F32;
    }
    .category-winner {
        margin-bottom: 2rem;
    }
    .medal {
        font-size: 1.2rem;
        margin-right: 0.5rem;
    }
    .leaderboard-title {
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        border: 1px solid #f0f0f0;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        color: #888;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Load configuration
@st.cache_data
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)


config = load_config()

# Passcode for app access - can be moved to config file later if desired
APP_PASSCODE = os.environ.get("APP_PASSCODE", "hackathon2025")


# Function to reload configuration
def reload_config():
    # Clear the cache to force reload
    load_config.clear()
    # Reload the config
    new_config = load_config()
    return new_config


# File to store scores
SCORES_FILE = "scores.json"


# Initialize or load scores
def initialize_or_load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as file:
            return json.load(file)
    else:
        return {"scores": {}}


# Save scores to JSON file
def save_scores(scores):
    with open(SCORES_FILE, "w") as file:
        json.dump(scores, file, indent=4)


# Function to load logo image
def load_logo(logo_path):
    if not logo_path:
        return None

    # Try different path options if the direct path doesn't work
    possible_paths = [
        logo_path,
        os.path.join(os.getcwd(), logo_path),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_path),
        logo_path.lstrip("./"),
    ]

    for path in possible_paths:
        try:
            if os.path.exists(path):
                return Image.open(path)
        except Exception:
            continue

    return None


# Helper function to calculate all teams average scores
def calculate_all_team_scores(scores_data):
    all_teams = config["teams"]
    all_categories = [cat["name"] for cat in config["categories"]]
    team_category_scores = {}

    # Initialize scores structure
    for team in all_teams:
        team_category_scores[team] = {}
        for category in all_categories:
            team_category_scores[team][category] = {
                "avg_score": 0,
                "total_possible": 0,
                "percentage": 0,
                "judges_count": 0,
            }

    if not scores_data["scores"]:
        return team_category_scores

    # Group scores by team
    for _, data in scores_data["scores"].items():
        team = data["team"]
        if team not in team_category_scores:
            continue

        # Calculate category scores
        for category, criteria_scores in data["scores"].items():
            if category not in team_category_scores[team]:
                continue

            # Get max possible score for this category
            category_max = sum(
                criterion["max_score"]
                for cat in config["categories"]
                if cat["name"] == category
                for criterion in cat["criteria"]
            )

            # Calculate total score for this category
            category_score = sum(criteria_scores.values())

            # Update the running totals
            current = team_category_scores[team][category]
            current["judges_count"] += 1

            # Calculate running average
            current_avg = current["avg_score"]
            new_avg = (
                (current_avg * (current["judges_count"] - 1)) + category_score
            ) / current["judges_count"]
            current["avg_score"] = new_avg
            current["total_possible"] = category_max
            current["percentage"] = (
                (new_avg / category_max * 100) if category_max > 0 else 0
            )

    return team_category_scores


# Helper function to get winners for each category
def get_category_winners(team_scores):
    category_winners = {}

    # Get all categories from config
    all_categories = [cat["name"] for cat in config["categories"]]

    for category in all_categories:
        # Create a list of (team, score) tuples for this category
        category_results = []
        for team, categories in team_scores.items():
            if category in categories and categories[category]["judges_count"] > 0:
                # Use percentage score for ranking
                category_results.append((team, categories[category]["percentage"]))

        # Sort by score (descending)
        category_results.sort(key=lambda x: x[1], reverse=True)

        # Store the results
        category_winners[category] = category_results

    return category_winners


# Streamlit app starts here
def main():
    # Check authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Show login screen if not authenticated
    if not st.session_state.authenticated:
        show_login_screen()
        return

    # Main app content - only shown after authentication
    scores_data = initialize_or_load_scores()

    # Initialize session state for team navigation
    if "current_team_index" not in st.session_state:
        st.session_state.current_team_index = 0

    # Sidebar for judge selection
    with st.sidebar:
        # Get event title and logo
        event_title = config.get("event", {}).get("title", "Hackathon Judging")
        logo_path = config.get("event", {}).get("logo_path", "")

        # Display logo in sidebar if available with custom HTML for centering
        logo_image = load_logo(logo_path)
        if logo_image:
            logo_html = f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{image_to_base64(logo_image)}" alt="{event_title} Logo">
            </div>
            """
            st.markdown(logo_html, unsafe_allow_html=True)

        # Display event title instead of generic "Hackathon Judge"
        st.markdown(
            f'<h1 class="event-title">🏆 {event_title}</h1>', unsafe_allow_html=True
        )

        # Judge selection
        judge = st.selectbox("Select your name:", config["judges"])
        st.markdown(
            f"<div class='judge-name' style='font-size: 1.2rem; font-weight: bold; color: #4285F4;'>Welcome, {judge}</div>",
            unsafe_allow_html=True,
        )

        # # Navigation
        # st.subheader("Dashboards")
        page = st.radio("", ["Judge Teams", "View Scores", "Leaderboard"])

        # Settings section with reload config button
        with st.expander("⚙️ Settings"):
            if st.button("Reload Configuration"):
                # Reload config without using global keyword
                load_config.clear()
                st.success("Configuration reloaded successfully!")
                st.rerun()

    # Main content
    if page == "Judge Teams":
        judge_teams(judge, scores_data)
    elif page == "View Scores":
        view_scores(scores_data)
    else:
        view_leaderboard(scores_data)


# Helper function to convert image to base64 for embedding in HTML
def image_to_base64(img):
    import base64
    import io

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def judge_teams(judge, scores_data):
    st.title("Judge Teams")

    # Get the team index from session state
    team_index = st.session_state.current_team_index
    teams = config["teams"]

    # Ensure team index is within valid range
    team_index = max(0, min(team_index, len(teams) - 1))

    # Team selection with automatic setting of index
    selected_index = st.selectbox(
        "Select team to judge:",
        range(len(teams)),
        format_func=lambda i: teams[i],
        index=team_index,
    )

    # Update the session state if user changes the dropdown
    if selected_index != team_index:
        st.session_state.current_team_index = selected_index
        team_index = selected_index

    team = teams[team_index]

    # Team navigation buttons - always visible
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if team_index > 0:
            if st.button("← Previous Team", key="prev_team", use_container_width=True):
                st.session_state.current_team_index = team_index - 1
                st.rerun()
    with col2:
        if team_index < len(teams) - 1:
            if st.button("Next Team →", key="next_team", use_container_width=True):
                st.session_state.current_team_index = team_index + 1
                st.rerun()

    st.markdown(
        f"<div class='team-name' style='font-size: 1.5rem; font-weight: bold; margin-bottom: 10px;'>{team}</div>",
        unsafe_allow_html=True,
    )

    # Create a form for each team to avoid accidental submission
    with st.form(key=f"team_form_{team}"):
        team_scores = {}

        # For each category
        for category in config["categories"]:
            st.markdown(
                f"<h2 style='font-size: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem;'>{category['name']}</h2>",
                unsafe_allow_html=True,
            )
            category_scores = {}

            # For each criterion in this category
            for criterion in category["criteria"]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f"<div style='font-size: 1.1rem; font-weight: bold;'>{criterion['name']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(criterion["description"])

                with col2:
                    score = st.slider(
                        f"{criterion['name']} score",
                        min_value=0,
                        max_value=criterion["max_score"],
                        value=0,
                        key=f"{team}_{category['name']}_{criterion['name']}",
                        label_visibility="collapsed",
                    )

                category_scores[criterion["name"]] = score

            team_scores[category["name"]] = category_scores
            st.markdown("<hr>", unsafe_allow_html=True)

        # Notes field moved to the end
        # st.markdown("<hr style='margin-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='font-size: 1.5rem; margin-top: 1rem; margin-bottom: 0.5rem;'>Additional Notes</h2>",
            unsafe_allow_html=True,
        )
        notes = st.text_area(
            "Add any additional comments about this team",
            key=f"notes_{team}",
            height=150,
        )

        submit_button = st.form_submit_button("Save Scores")

        if submit_button:
            # Create unique key for this judge and team
            judge_key = f"{judge}_{team}"

            # Store scores with timestamp
            scores_data["scores"][judge_key] = {
                "judge": judge,
                "team": team,
                "scores": team_scores,
                "notes": notes,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            save_scores(scores_data)
            st.success(f"Scores saved for {team}!")

    # Bottom navigation buttons - also always visible
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if team_index > 0:
            if st.button(
                "← Previous Team", key="prev_team_bottom", use_container_width=True
            ):
                st.session_state.current_team_index = team_index - 1
                st.rerun()
    with col2:
        if team_index < len(teams) - 1:
            if st.button(
                "Next Team →", key="next_team_bottom", use_container_width=True
            ):
                st.session_state.current_team_index = team_index + 1
                st.rerun()


def view_scores(scores_data):
    st.title("Team Scores")

    if not scores_data["scores"]:
        st.info("No scores have been submitted yet.")
        return

    # Team selection for viewing scores
    teams = list(
        set(score_data["team"] for score_data in scores_data["scores"].values())
    )
    team = st.selectbox(
        "Select team to view scores:", teams if teams else ["No teams scored yet"]
    )

    if not teams:
        return

    st.markdown(
        f"<div style='font-size: 1.5rem; font-weight: bold; margin-bottom: 10px;'>{team}</div>",
        unsafe_allow_html=True,
    )

    # Filter scores for selected team
    team_scores = {k: v for k, v in scores_data["scores"].items() if v["team"] == team}

    if not team_scores:
        st.info(f"No scores available for {team}.")
        return

    # Display scores by judge
    for judge_key, data in team_scores.items():
        with st.expander(f"Scores by {data['judge']} - {data['timestamp']}"):
            # Display scores by category
            for category, criteria_scores in data["scores"].items():
                st.markdown(
                    f"<h2 style='font-size: 1.5rem; margin-top: 1rem; margin-bottom: 0.5rem;'>{category}</h2>",
                    unsafe_allow_html=True,
                )

                # Calculate category total
                category_max = sum(
                    criterion["max_score"]
                    for cat in config["categories"]
                    if cat["name"] == category
                    for criterion in cat["criteria"]
                )
                category_score = sum(criteria_scores.values())

                # Display progress bar for category total
                st.caption(f"Total: {category_score}/{category_max}")
                st.progress(category_score / category_max if category_max > 0 else 0)

                # Display individual criteria scores
                for criterion, score in criteria_scores.items():
                    criterion_config = next(
                        (
                            c
                            for cat in config["categories"]
                            if cat["name"] == category
                            for c in cat["criteria"]
                            if c["name"] == criterion
                        ),
                        None,
                    )
                    if criterion_config:
                        max_score = criterion_config["max_score"]
                        st.caption(f"{criterion}: {score}/{max_score}")

            # Display notes if available
            if data["notes"]:
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader("Notes")
                st.write(data["notes"])

    # Calculate and display team averages
    st.subheader("Team Average Scores")

    # Organize scores by category and criterion
    categories = config["categories"]
    avg_scores = {}

    for category in categories:
        cat_name = category["name"]
        avg_scores[cat_name] = {}

        for criterion in category["criteria"]:
            crit_name = criterion["name"]
            scores = [
                data["scores"].get(cat_name, {}).get(crit_name, 0)
                for data in team_scores.values()
                if cat_name in data["scores"] and crit_name in data["scores"][cat_name]
            ]

            if scores:
                avg_scores[cat_name][crit_name] = sum(scores) / len(scores)
            else:
                avg_scores[cat_name][crit_name] = 0

    # Display average scores
    for category in categories:
        cat_name = category["name"]
        if cat_name in avg_scores:
            st.markdown(
                f"<h2 style='font-size: 1.5rem; margin-top: 1rem; margin-bottom: 0.5rem;'>{cat_name}</h2>",
                unsafe_allow_html=True,
            )

            # Calculate category total and max
            cat_scores = avg_scores[cat_name]
            cat_total = sum(cat_scores.values())
            cat_max = sum(criterion["max_score"] for criterion in category["criteria"])

            # Display progress bar for category total
            st.caption(f"Average Total: {cat_total:.1f}/{cat_max}")
            st.progress(cat_total / cat_max if cat_max > 0 else 0)

            # Display individual criteria averages
            for criterion in category["criteria"]:
                crit_name = criterion["name"]
                if crit_name in cat_scores:
                    max_score = criterion["max_score"]
                    avg = cat_scores[crit_name]
                    st.caption(f"{crit_name}: {avg:.1f}/{max_score}")


def view_leaderboard(scores_data):
    st.markdown(
        "<h1 class='leaderboard-title'>🏆 Hackathon Leaderboard</h1>",
        unsafe_allow_html=True,
    )

    if not scores_data["scores"]:
        st.info(
            "No scores have been submitted yet. The leaderboard will be available once judges start scoring."
        )
        return

    # Calculate all team scores
    team_scores = calculate_all_team_scores(scores_data)

    # Get category winners
    category_winners = get_category_winners(team_scores)

    # Show overall stats
    st.subheader("Judging Progress")
    col1, col2, col3 = st.columns(3)

    with col1:
        total_teams = len(config["teams"])
        judged_teams = len(set(data["team"] for data in scores_data["scores"].values()))

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Teams Judged</div>
                <div class="metric-value">{judged_teams}/{total_teams}</div>
                <div class="metric-label">{int(judged_teams / total_teams * 100 if total_teams > 0 else 0)}% Complete</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        total_scores = len(scores_data["scores"])
        judges_participated = len(
            set(data["judge"] for data in scores_data["scores"].values())
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Judges Participated</div>
                <div class="metric-value">{judges_participated}/{len(config["judges"])}</div>
                <div class="metric-label">{total_scores} Scoring Sessions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        avg_score = 0
        score_count = 0
        for team_data in team_scores.values():
            for cat_data in team_data.values():
                if cat_data["judges_count"] > 0:
                    avg_score += cat_data["percentage"]
                    score_count += 1

        if score_count > 0:
            avg_score = avg_score / score_count

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Across All Categories</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Display category winners
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Category Leaders")

    for category, winners in category_winners.items():
        st.markdown(f"<h3>{category}</h3>", unsafe_allow_html=True)

        if not winners:
            st.write("No teams have been judged in this category yet.")
            continue

        # Create a DataFrame for this category
        winners_df = pd.DataFrame(winners, columns=["Team", "Score"])
        winners_df["Score"] = winners_df["Score"].map(lambda x: f"{x:.1f}%")

        # Show top 3 teams
        top_teams = min(3, len(winners))
        cols = st.columns(top_teams)

        for i in range(top_teams):
            with cols[i]:
                team, score = winners[i]
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"

                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">#{i + 1} Place</div>
                        <div class="medal">{medal}</div>
                        <div class="metric-value" style="font-size: 1.5rem;">{team}</div>
                        <div class="metric-label">Score: {winners_df.iloc[i]["Score"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Show full leaderboard in an expander
        with st.expander("View Full Leaderboard"):
            # Add ranking column
            winners_df.insert(0, "Rank", range(1, len(winners_df) + 1))
            st.table(winners_df)

        st.markdown("<hr>", unsafe_allow_html=True)

    # Overall Winners
    st.subheader("Overall Standings")

    # Calculate overall scores
    overall_scores = []
    for team, categories in team_scores.items():
        total_score = 0
        total_categories = 0

        for category, data in categories.items():
            if data["judges_count"] > 0:
                total_score += data["percentage"]
                total_categories += 1

        if total_categories > 0:
            avg_score = total_score / total_categories
            overall_scores.append((team, avg_score, total_categories))

    if not overall_scores:
        st.write("No teams have been fully judged yet.")
    else:
        # Sort by score (descending)
        overall_scores.sort(key=lambda x: x[1], reverse=True)

        # Create a DataFrame
        df = pd.DataFrame(
            overall_scores, columns=["Team", "Overall Score", "Categories Judged"]
        )
        df["Overall Score"] = df["Overall Score"].map(lambda x: f"{x:.1f}%")
        df.insert(0, "Rank", range(1, len(df) + 1))

        # Show top 3 teams
        top_teams = min(3, len(overall_scores))
        cols = st.columns(top_teams)

        for i in range(top_teams):
            with cols[i]:
                team, score, cats = overall_scores[i]
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"

                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">#{i + 1} Overall</div>
                        <div class="medal">{medal}</div>
                        <div class="metric-value" style="font-size: 1.5rem;">{team}</div>
                        <div class="metric-label">Score: {df.iloc[i]["Overall Score"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Show full standings
        st.table(df)


# Login screen
def show_login_screen():
    st.title("🔒 Hackathon Judge Login")

    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Get event title from config
        event_title = config.get("event", {}).get("title", "Hackathon Judging")
        logo_path = config.get("event", {}).get("logo_path", "")

        # Display logo if available
        logo_image = load_logo(logo_path)
        if logo_image:
            logo_html = f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{image_to_base64(logo_image)}" alt="{event_title} Logo" style="max-width: 300px;">
            </div>
            """
            st.markdown(logo_html, unsafe_allow_html=True)

        # Passcode input field
        passcode = st.text_input("Enter passcode:", type="password")

        if st.button("Login"):
            if passcode == APP_PASSCODE:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect passcode. Please try again.")


if __name__ == "__main__":
    main()
