import pygame
import random
import math
import requests
import io
import syncedlyrics
import re
import colorgram
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="PASTE-CLIENT-ID", #Copy from Spotify APP
    client_secret="PASTE-CLIENT-SECRET", #Copy from Spotify APP
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-read-currently-playing"
))

#Initial configuration
WIDTH, HEIGHT = 1920, 1080 #Screen dimensions
NUM_BLOBS = 30  #Blobs number
BLOB_RADIUS_MIN = 350 #Min blob radius
BLOB_RADIUS_MAX = 550 #Max blob radius
SPEED = 1  #Blob speed 

#Colors
COLORS = [ #Default colors in case album colors can't be fetched
    (255, 0, 150),   
    (0, 200, 255),  
    (100, 0, 255),   
    (255, 100, 50),  
    (50, 50, 200),   
    (0, 255, 100),   
    (200, 50, 255),  
]

class Blob:
    def __init__(self, screen_w, screen_h):
        self.radius = random.randint(BLOB_RADIUS_MIN, BLOB_RADIUS_MAX)
        self.x = random.randint(0, screen_w)
        self.y = random.randint(0, screen_h)
        
        self.dx = random.choice([-1, 1]) * random.uniform(0.05, SPEED)
        self.dy = random.choice([-1, 1]) * random.uniform(0.05, SPEED)
        
        self.color = random.choice(COLORS)
        self.surface = self._create_gradient_surface()

    def _create_gradient_surface(self):
        
        surf_size = self.radius * 2
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        
        for r in range(self.radius, 0, -3):
            alpha_ratio = (1 - (r / self.radius))
           
            alpha = int(alpha_ratio**1.5 * 100)
            
            pygame.draw.circle(surf, (self.color[0], self.color[1], self.color[2], alpha), (self.radius, self.radius), r)
        return surf

    def move(self, w, h):
        self.x += self.dx
        self.y += self.dy

        if self.x < -self.radius // 3 or self.x > w + self.radius // 3:
            self.dx *= -1
        if self.y < -self.radius // 3 or self.y > h + self.radius // 3:
            self.dy *= -1

    def draw(self, screen):
        screen.blit(self.surface, (int(self.x - self.radius), int(self.y - self.radius)))

def update_track_image(current_track): #Fetch and prepare track image
    track_image_url = current_track['item']['album']['images'][0]['url'] #Get album image URL
    track_image_request = requests.get(track_image_url) #Request the image
    track_image_file = io.BytesIO(track_image_request.content) #Load image into BytesIO
    track_image = pygame.image.load(track_image_file).convert_alpha() #Load image with Pygame
    track_image_resized = pygame.transform.smoothscale(track_image, (400, 400)) #Resize image
    return track_image_resized

def update_song_info(current_track, font): #Fetch and prepare song info
    # Titulo cancion
    song_name = current_track['item']['name'] #Get song name
    song_text = font.render(song_name, True, (255, 255, 255)) #Render song name
    song_text_rect = song_text.get_rect(center=(WIDTH // 4, 800)) #Get rect for positioning

    # Artista cancion
    artist_name = current_track['item']['artists'][0]['name'] #Get artist name
    artist_text = font.render(artist_name, True, (200, 200, 200)) #Render artist name
    artist_text_rect = artist_text.get_rect(center=(WIDTH // 4, 870)) #Get rect for positioning
    
    return song_text, song_text_rect, artist_text, artist_text_rect

def new_lyrics(current_track, font): #Fetch and prepare new lyrics
    song = current_track['item']['name'] #Get song name
    artist = current_track['item']['artists'][0]['name'] #Get artist name

    search_term = f"{song} {artist}" #Create search term
    lyrics = syncedlyrics.search(search_term) #Search for lyrics
    lyrics_list = lyrics.split('\n') #Split lyrics into lines
    separate_lyrics = [] #List to hold time-text pairs

    for line in lyrics_list:
        mins, secs, cents, text = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', line).groups() #Extract time and text
        total_ms = (int(mins) * 60 * 1000) + (int(secs) * 1000) + (int(cents) * 10) #Convert time to milliseconds
        separate_lyrics.append({'time': total_ms, 'text': text.strip()}) #Add to list

    lyrics = [] #List to hold rendered lyric surfaces
    for entry in separate_lyrics:
        entry_text = font.render(entry['text'], True, (255, 255, 255)) #Render lyric text
        lyrics.append(entry_text) #Add to list
    
    lyrics_rects = [] #List to hold lyric rects
    for lyric in lyrics:
        lyrics_rects.append(lyric.get_rect(center=(WIDTH // 4 + WIDTH // 2, HEIGHT // 2))) #Position rects

    return separate_lyrics, lyrics, lyrics_rects
    
def render_wrapped_text(text, font, color, max_width): #Render text with word wrapping
    words = text.split(' ') #Split text into words
    lines = [] #List to hold lines
    current_line = [] #Current line words

    for word in words: #For each word
        test_line = ' '.join(current_line + [word]) #Create test line
        width, height = font.size(test_line) #Get size of test line

        if width < max_width: #If it fits
            current_line.append(word) #Add word to current line
        else:
            lines.append(' '.join(current_line)) #Add current line to lines
            current_line = [word] #Start new line with current word

    lines.append(' '.join(current_line)) #Add last line

    surfaces = [] #List to hold rendered line surfaces
    for line in lines: 
        surfaces.append(font.render(line, True, color)) #Render each line and add to list

    return surfaces

def get_album_colors(current_track):
    track_image_url = current_track['item']['album']['images'][0]['url'] #Get album image URL
    track_image_request = requests.get(track_image_url) #Request the image
    track_image_file = io.BytesIO(track_image_request.content) #Load image into BytesIO
    track_image = pygame.image.load(track_image_file).convert_alpha() #Load image with Pygame
    
   
    temp_image_path = "temp_track_image.jpg" #Temporary path to save image
    pygame.image.save(track_image, temp_image_path) #Save image temporarily
    
    colors = colorgram.extract(temp_image_path, 6) #Extract colors using colorgram
    
    extracted_colors = [] #List to hold extracted colors
    for color in colors: #For each extracted color
        r, g, b = color.rgb #Get RGB values
        extracted_colors.append((r, g, b))  #Add to list
    
    return extracted_colors

def main():
    pygame.init() #Initialize Pygame
    screen = pygame.display.set_mode((WIDTH, HEIGHT)) #Create screen
    pygame.display.set_caption("Spotify Visuals") #Set window title
    clock = pygame.time.Clock() #Create clock for framerate control
    current_track = sp.current_user_playing_track() #Initial track fetch

    #Timers
    spotifyapi_timer = pygame.USEREVENT + 1 #Timer for Spotify API
    pygame.time.set_timer(spotifyapi_timer, 500)  #Every 500 ms

    #Font load
    font = pygame.font.Font("fonts/Outfit-Medium.ttf", 50) #Load font

    #Create blobs
    blobs = [Blob(WIDTH, HEIGHT) for _ in range(NUM_BLOBS)] 

    #Track image load
    track_image_url = "https://i.scdn.co/image/ab67616d0000b2736275aeac316378b0dd4f31fd" 
    track_image_request = requests.get(track_image_url)
    track_image_file = io.BytesIO(track_image_request.content)
    track_image = pygame.image.load(track_image_file).convert_alpha()
    track_image_resized = pygame.transform.smoothscale(track_image, (400, 400))
    track_image_rect = track_image_resized.get_rect(center=(WIDTH // 4, 540))

    # Song title
    song_name = "T-Shirt"
    song_text = font.render(song_name, True, (255, 255, 255))
    song_text_rect = song_text.get_rect(center=(WIDTH // 4, 800))

    # song artist
    artist_name = "Migos"
    artist_text = font.render(artist_name, True, (200, 200, 200))
    artist_text_rect = artist_text.get_rect(center=(WIDTH // 4, 870))

    # Lyrics variables
    separate_lyrics = [
    {'time': 1000, 'text': "--- INICIO (1.0s) ---"},
    {'time': 3000, 'text': "Debería salir a los 3 segundos"},
    {'time': 5000, 'text': "Debería salir a los 5 segundos"},
    {'time': 7000, 'text': "Debería salir a los 7 segundos"},
    {'time': 9000, 'text': "Debería salir a los 9 segundos"},
    {'time': 11000, 'text': "Debería salir a los 11 segundos"},
    {'time': 13000, 'text': "--- FIN (13.0s) ---"}]

    lyrics = []
    for entry in separate_lyrics:
        entry_text = font.render(entry['text'], True, (255, 255, 255))
        lyrics.append(entry_text)
    
    lyrics_rects = []
    for lyric in lyrics:
        lyrics_rects.append(lyric.get_rect(center=(WIDTH // 4 + WIDTH // 2, HEIGHT // 2)))


    last_trackid = None #To track changes in the song

    running = True #Main loop flag
    while running:
        for event in pygame.event.get(): #Event handling
            if event.type == pygame.QUIT: #Quit event
                running = False

            if event.type == spotifyapi_timer: #Spotify API timer event every 500 ms
                if current_track:
                    current_track = sp.current_user_playing_track() #Fetch current track
                    if current_track['item']['id'] != last_trackid: #If track has changed
                        last_trackid = current_track['item']['id'] #Update last track ID

                        # Update track image and song info
                        track_image_resized = update_track_image(current_track) #Fetch and prepare track image
                        song_text, song_text_rect, artist_text, artist_text_rect = update_song_info(current_track, font) #Fetch and prepare song info
                        separate_lyrics, lyrics, lyrics_rects = new_lyrics(current_track, font) #Fetch and prepare new lyrics

                        #Update colors
                        global COLORS
                        COLORS = get_album_colors(current_track) #Extract colors from album art
                        blobs = [Blob(WIDTH, HEIGHT) for _ in range(NUM_BLOBS)] #Recreate blobs with new colors

        screen.fill((0, 0, 0)) #Clear screen

        for blob in blobs:
            blob.move(WIDTH, HEIGHT) #Move blob
            blob.draw(screen) #Draw blob
        
        #Draw track image
        screen.blit(track_image_resized, track_image_rect)

        #Draw song and artist text
        screen.blit(song_text, song_text_rect)
        screen.blit(artist_text, artist_text_rect)

        try: 
            for i, entry in enumerate(separate_lyrics): #Draw lyrics synchronized with music
                current_time_ms = current_track['progress_ms'] #Get current track progress in ms
                
                if current_time_ms < separate_lyrics[i + 1]["time"] and current_time_ms >= entry['time']: #If within the time range for this lyric
                    
                    #Prepare lyric text
                    raw_text = entry['text']
                    
                    #Rendering with wrapping
                    wrapped_lines = render_wrapped_text(raw_text, font, (255, 255, 255), WIDTH // 2.5)
                    
                    #Line height and total height calculation
                    line_height = 60
                    total_height = len(wrapped_lines) * line_height
                    
                    #Horizontal position (X)
                    target_x = (WIDTH // 4) * 3
                    
                    #Vertical position (Y)
                    target_y = HEIGHT // 2
                    
                    #Calculate starting Y position to center the block of text
                    start_y = target_y - (total_height // 2)

                    #Draw each wrapped line
                    for j, line_surface in enumerate(wrapped_lines):
                        line_rect = line_surface.get_rect()
                        
                        #Position each line
                        line_rect.centerx = target_x 
                        line_rect.y = start_y + (j * line_height)
                        
                        screen.blit(line_surface, line_rect)
        except IndexError:
            pass
            
        pygame.display.flip() #Update display
        clock.tick(60) #Maintain 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()

