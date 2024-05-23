from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def format_anime_name(name):
    return name.lower().replace(' ', '-')

@app.route('/')
def index():
    episode = request.args.get('episode', '90')
    embed_url = f"https://2anime.xyz/embed/one-piece-episode-{episode}"
    return render_template('index.html', embed_url=embed_url, episode=episode, episode_start=int(episode))

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        formatted_name = format_anime_name(query)
        return redirect(url_for('anime', name=formatted_name))
    return redirect(url_for('index'))

@app.route('/anime/<name>')
def anime(name):
    episode = request.args.get('episode', '1')
    episode_start = int(episode) // 100 * 100 + 1
    embed_url = f"https://2anime.xyz/embed/{name}-episode-{episode}"
    return render_template('anime.html', embed_url=embed_url, anime_name=name, episode=episode, episode_start=episode_start)

if __name__ == '__main__':
    app.run(debug=True)
