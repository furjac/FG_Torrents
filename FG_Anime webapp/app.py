from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)

def format_anime_name(name):
    return name.lower().replace(' ', '-')

@app.route('/')
def index():
    episode = int(request.args.get('episode', '1'))
    episode_type = request.args.get('type', 'sub')
    embed_url = f"https://2anime.xyz/embed/one-piece{'-dub' if episode_type == 'dub' else ''}-episode-{episode}"
    response = make_response(render_template('index.html', embed_url=embed_url, episode=episode, episode_start=(episode - 1) // 100 * 100 + 1, episode_type=episode_type))
    response.set_cookie('last_episode', str(episode), max_age=30*24*60*60)  # Save for 30 days
    return response

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        formatted_name = format_anime_name(query)
        return redirect(url_for('anime', name=formatted_name))
    return redirect(url_for('index'))

@app.route('/anime/<name>')
def anime(name):
    episode = int(request.args.get('episode', request.cookies.get('last_episode', '1')))
    episode_type = request.args.get('type', 'sub')
    episode_start = (episode - 1) // 100 * 100 + 1
    embed_url = f"https://2anime.xyz/embed/{name}{'-dub' if episode_type == 'dub' else ''}-episode-{episode}"
    response = make_response(render_template('anime.html', embed_url=embed_url, anime_name=name, episode=episode, episode_start=episode_start, episode_type=episode_type))
    response.set_cookie(f'{name}_last_episode', str(episode), max_age=30*24*60*60)  # Save for 30 days
    return response

if __name__ == '__main__':
    app.run(debug=True)
