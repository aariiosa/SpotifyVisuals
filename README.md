# SpotifyVisuals
An app that shows Spotify's current playing song with its lyrics.

## Description
This app connects to the Spotify API to get the user's current playing song data. It displays the album photo, name, artist, and synchronized lyrics.

## Requirements
- Libraries: pygame, random, math, requests, io, syncedlyrics, re, colorgram and spotipy.

- A Spotify APP which you can create [here](https://developer.spotify.com/documentation/web-api/concepts/apps)

## Installation
1. Create your Spotify APP
2. Put your app's client id and client secret (line 12)
```python
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="PASTE-CLIENT-ID", #Copy from Spotify APP
    client_secret="PASTE-CLIENT-SECRET", #Copy from Spotify APP
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-read-currently-playing"
))
```
3. Now you can start the program and login into your Spotify account.