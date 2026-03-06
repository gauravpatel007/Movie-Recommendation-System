import streamlit as st
import pickle
import pandas as pd
import requests

# Set wide layout and title
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .movie-card {
        background-color: #2b2b2b;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .movie-title {
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 5px;
        color: #ffffff;
    }
    .movie-meta {
        font-size: 0.9rem;
        color: #b3b3b3;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Cache data loading for speed
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movie_dict.pkl','rb'))
    movies_df = pd.DataFrame(movies_dict)
    similarity_matrix = pickle.load(open('similarity.pkl','rb'))
    return movies_df, similarity_matrix

try:
    movies, similarity = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}. Please ensure 'movie_dict.pkl' and 'similarity.pkl' exist.")
    st.stop()

# Function to fetch comprehensive movie details from TMDB API
@st.cache_data
def fetch_movie_details(movie_id):
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    try:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US')
        response.raise_for_status()
        data = response.json()
        
        poster_path = data.get('poster_path')
        full_poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Poster+Available"
        
        genres_list = [genre['name'] for genre in data.get('genres', [])]
        
        return {
            'poster': full_poster_url,
            'rating': data.get('vote_average', 'N/A'),
            'runtime': data.get('runtime', 'N/A'),
            'release_year': data.get('release_date', 'N/A')[:4] if data.get('release_date') else 'N/A',
            'overview': data.get('overview', 'No overview available.').strip() or 'No overview available.',
            'genres': genres_list
        }
    except Exception as e:
        return {
            'poster': "https://via.placeholder.com/500x750?text=Error+Fetching+Data",
            'rating': 'N/A',
            'runtime': 'N/A',
            'release_year': 'N/A',
            'overview': 'Could not fetch details.',
            'genres': []
        }

# Function to recommend movies
def recommend(movie, num_recommendations=5):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    
    # Exclude the first item which is the movie itself (dist=1.0)
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num_recommendations+1]
    
    recommended_movies = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_movie_details(movie_id)
        details['title'] = movies.iloc[i[0]].title
        recommended_movies.append(details)
        
    return recommended_movies

# --- APP UI START ---

# Sidebar for Settings
with st.sidebar:
    st.title("⚙️ Preferences")
    
    selected_movie_name = st.selectbox(
        'Select a movie you love:',
        movies['title'].values
    )
    
    num_recs = st.slider('Number of recommendations:', min_value=5, max_value=15, value=5, step=5)
    
    st.markdown("---")
    recommend_button = st.button('Get Recommendations', use_container_width=True, type='primary')
    
    st.markdown("""
        <div style='margin-top: 50px;'>
            <small style='color: gray;'>Data provided by TMDB.</small>
        </div>
    """, unsafe_allow_html=True)


# Main Body (Hero Section)
st.title('🎬 Advanced Movie Recommender')
st.markdown("Discover movies tailored to your taste with detailed insights, ratings, and gorgeous posters.")
st.divider()

if selected_movie_name:
    # Find ID of selected movie to fetch details
    movie_id = movies[movies['title'] == selected_movie_name].iloc[0].movie_id
    
    with st.spinner("Fetching movie magic..."):
        selected_details = fetch_movie_details(movie_id)
        
    # Layout for Hero Section
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        st.image(selected_details['poster'], use_container_width=True)
        
    with col2:
        st.header(selected_movie_name)
        st.caption(f"⭐ **{selected_details['rating']}/10** &nbsp; | &nbsp; 📅 **{selected_details['release_year']}** &nbsp; | &nbsp; ⏱️ **{selected_details['runtime']} mins**")
        
        if selected_details['genres']:
            st.markdown(f"**Genres:** {', '.join(selected_details['genres'])}")
            
        st.write("---")
        st.write("**Overview:**")
        st.write(selected_details['overview'])

st.divider()

# Recommendations Section
if recommend_button:
    st.header(f"Because you liked **{selected_movie_name}**...")
    
    with st.spinner(f"Curating {num_recs} recommendations for you..."):
        recommendations = recommend(selected_movie_name, num_recs)
    
    # Display in a responsive grid format (up to 5 per row)
    cols_per_row = 5
    for i in range(0, len(recommendations), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(recommendations):
                rec = recommendations[i + j]
                with col:
                    st.image(rec['poster'], use_container_width=True)
                    st.markdown(f"""
                        <div style='margin-top: 10px; margin-bottom: 5px; min-height: 40px;'>
                            <strong>{rec['title']}</strong>
                        </div>
                        <div style='color: gray; font-size: 0.85em; margin-bottom: 10px;'>
                            ⭐ {rec['rating']} | 📅 {rec['release_year']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("More details"):
                        st.write("🎭 **" + ", ".join(rec['genres'][:3]) + "**")
                        st.caption(f"Overview: {rec['overview']}")