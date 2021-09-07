from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk, ImageChops
import tkinter as tk
import configparser
import pyautogui
import spotipy
import urllib3
import time
import io

config = configparser.ConfigParser()
config.read("config.ini")
client_id = config["Keys"]["client_id"]
client_secret = config["Keys"]["client_secret"]

# Font
font = config["Config"]["font_name"]
font_size = int(config["Config"]["font_size"])

# Positions
vertical_pos = config["Config"]["vertical_pos"]
horizontal_pos = config["Config"]["horizontal_pos"]
img_pos = config["Config"]["image_pos"]

sp_data = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri="http://localhost", scope="user-read-playback-state"))


def add_0(t):
    if len(t) == 1:
        t = '0' + str(t)
    return t


def convert_ms(ms):
    seconds = add_0(str(int((ms / 1000) % 60)))
    minutes = str(int((ms / (1000 * 60)) % 60))

    return f"{minutes}:{seconds}"


class Overlay:
    def __init__(self):
        self.is_hidden = True
        self.win = tk.Tk()
        self.win.title = "Spotify Overlay"
        self.tk_var = tk.StringVar()
        self.tk_var.set("Loading...")
        self.lab = tk.Label(self.win, textvariable=self.tk_var, bg="#808080", fg="#FFFFFF", font=(font, font_size))  # Loading box
        self.lab.place(x=0, y=0)  # Place the Loading box
        self.lab_img_url = None
        self.win.attributes("-topmost", True)  # The tkinter is always on top of the screen
        self.win.attributes("-alpha", 0.8)
        self.win.overrideredirect(True)  # Removes top buttons and unable to close tkinter- also sticks to top
        self.width = self.win.winfo_screenwidth()
        self.height = self.win.winfo_screenheight()
        self.mouse_pos = pyautogui.position()
        # self.hide()  # First time until loads song.
        self.updater()

        self.win.mainloop()

    def updater(self):
        self.mouse_pos = pyautogui.position()
        if self.mouse_in_box():
            self.hide()
            while self.mouse_in_box():
                self.mouse_pos = pyautogui.position()

        while True:
            data = sp_data.current_user_playing_track()
            if not data:
                time.sleep(5)
                continue
            break
        if not data["is_playing"]:  # Song is paused
            self.hide()  # Hide overlay
        elif self.is_hidden:
            self.show()
        artists = []

        # print(data)
        self.ensure_image_state(data["item"]["album"]["images"][2]["url"])
        self.refresh_res()

        song_name = data["item"]["name"]
        self.lab_img_url = None
        if len(data["item"]["artists"]) > 1:
            for artist in data["item"]["artists"]:
                artists.append(artist["name"])
            artist = ", ".join(artists)
        else:
            artist = data["item"]["artists"][0]["name"]
        self.update_win_res()
        progress = convert_ms(data["progress_ms"])  # How much I'm in the song
        length = convert_ms(data["item"]["duration_ms"])  # Song total length
        self.tk_var.set(f"playing:\n{song_name}\n By: {artist}\n{progress} / {length}")
        self.win.after(700, self.updater)

    def mouse_in_box(self):
        win_x = int(self.win.geometry().split("+")[1])
        win_y = int(self.win.geometry().split("+")[2])
        win_x_ofs = int(self.win.geometry().split("x")[0])
        win_y_ofs = int(self.win.geometry().split("x")[1].split("+")[0])
        tl = (win_x, win_y)
        br = (win_x + win_x_ofs, win_y + win_y_ofs)
        if (tl[0] < self.mouse_pos.x < br[0]) and (tl[1] < self.mouse_pos.y < br[1]):
            return True
        return False

    def hide(self):
        self.win.withdraw()
        self.is_hidden = True

    def show(self):
        self.win.update()
        self.win.deiconify()
        self.is_hidden = False

    def update_image(self, url):
        small = urllib3.PoolManager().request("GET", url)
        img = ImageTk.PhotoImage((Image.open(io.BytesIO(small.data))))
        accent = self.get_img_cc(small)
        inv_accent = self.get_inv_img_cc(small)
        self.lab.img = img
        self.lab_img_url = url
        text_color = (0, 0, 0)
        if accent[0] <= 20 and accent[1] <= 20 and accent[2] <= 20:
            text_color = (255, 255, 255)
        self.lab.configure(textvariable=self.tk_var, image=img, compound=img_pos,
                           bg=self.rgb2hex(accent[0], accent[1], accent[2]),
                           fg=self.rgb2hex(text_color[0], text_color[1], text_color[2]))  # self.rgb2hex(inv_accept[0], inv_accept[1], inv_accept[2]

    def ensure_image_state(self, url):
        if url != self.lab_img_url:
            self.update_image(url)

    @staticmethod
    def rgb2hex(r, g, b):
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def refresh_res(self) -> None:
        self.width = self.win.winfo_screenwidth()
        self.height = self.win.winfo_screenheight()

    @staticmethod
    def get_img_cc(content):  # Get Image Color Coded
        img = Image.open(io.BytesIO(content.data))
        img.convert("RGB")
        img.resize((1, 1), resample=0)
        dominant_color = img.getpixel((0, 0))
        return dominant_color

    @staticmethod
    def get_inv_img_cc(content):
        img = Image.open(io.BytesIO(content.data))
        inv_img = ImageChops.invert(img)
        inv_img.convert("RGB")
        inv_img.resize((1, 1), resample=0)
        inv_dominant_color = inv_img.getpixel((0, 0))
        return inv_dominant_color

    def update_win_res(self):
        if horizontal_pos.lower() == "left":
            w = 15
        elif horizontal_pos.lower() == "right":
            w = (int(self.width)) - self.lab.winfo_width() - 15
        else:
            w = 30
        if vertical_pos.lower() == "bottom":
            h = int(self.height - self.height * 0.15)
        elif vertical_pos.lower() == "top":
            h = int(self.height - self.height * 0.95)
        else:
            h = (int(self.height)) / 2
        self.win.geometry(f"{self.lab.winfo_width()}x{self.lab.winfo_height()}+{w}+{h}")


if __name__ == "__main__":
    Overlay()
