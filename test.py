import requests

# Search for the anime by name
search_query = "one piece"
search_url = f"https://kitsu.io/api/edge/anime?filter[text]={search_query}"
search_response = requests.get(search_url)
search_data = search_response.json()

# Check if data is available and extract the first anime entry
if search_data['data']:
    anime_data = search_data['data'][0]['attributes']
    total_episodes = anime_data.get('episodeCount')
    synopsis = anime_data.get('synopsis', 'No synopsis available.')
    start_date = anime_data.get('startDate', 'No start date available.')
    status = anime_data.get('status', 'No status available.')
    rating = anime_data.get('averageRating', 'No rating available.')

    # Handle case where total episodes might be None
    if total_episodes is None:
        total_episodes = "Total episodes not specified."

    print(f"Title: One Piece")
    print(f"Total Episodes: {total_episodes}")
    print(f"Synopsis: {synopsis}")
    print(f"Start Date: {start_date}")
    print(f"Status: {status}")
    print(f"Average Rating: {rating}")
else:
    print("Anime not found.")
