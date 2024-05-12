from tkinter import (
	Tk,
	Label,
	Button,
	Canvas,
	Frame,
	filedialog,
	BooleanVar,
	StringVar,
	PhotoImage,
)

import os
import wave
from time import time
from io import BytesIO
from PIL import ImageTk
from threading import Thread
from datetime import datetime
from pickle import load as pkload

from pydub import AudioSegment
from pyaudio import PyAudio, paInt16

__author__ = "Im Geek"
__github__ = "https://github.com/imegeek/voice-recorder"
__version__ = 1.0

recording_save_path = "recordings"

# Create directory "recordings" if not exists.
if not os.path.isdir(recording_save_path):
	os.mkdir(recording_save_path)

# Create object
root = Tk()
root.title("Voice Recorder")
root.resizable(0, 0)

window_width = 800
window_height = 500

# Get the screen width and height.
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the center coordinates for positioning the window.
x_coordinate = int((screen_width/2) - (window_width/2))
y_coordinate = int((screen_height/2) - (window_height/2))

# Set the geometry of the window to be centered on the screen.
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
root.iconbitmap("src/icon.ico")

def close_window():
	window_alert.set("stop")
	root.update()

	if recording.get():
		animate.set(False)
		recording.set(False)

		# Continuously updates the root unit the 'record_finish' flag is set to True.
		while not record_finish.get():
			root.update()

	root.destroy()

root.protocol("WM_DELETE_WINDOW", close_window)

# Load images data
image_data = pkload(open("src/assets.dat", "rb"))

bg_image = ImageTk.PhotoImage(image_data[0])
mic_image = ImageTk.PhotoImage(image_data[1])

wave_path = "src/wave.gif"
wave_frames = image_data[-1]
wave_gif = [
	PhotoImage(file=wave_path, format=f"gif -index {frame}")
	for frame in range(wave_frames)
	]

def update_root(count=0):
	global mic_wave

	# Continuously repeat wave gif frames when flag is True
	if animate.get():
		mic_wave = wave_gif[count]
		count += 1
		if count == wave_frames:
			count = 0
	else:
		mic_wave = mic_image
	
	frame.itemconfig(mic, image=mic_wave)
	root.after(80, update_root, count)

def play_recording(path, file):
	if os.path.exists(path):
		audio_type = os.path.splitext(path)[-1]

		# Set chunk size of 1024 samples per data frame
		chunk = 1024

		if audio_type == ".wav":
			# Open the sound file
			wf = wave.open(path, 'rb')

			# Create an interface to PyAudio
			p = PyAudio()

			# 'output = True' indicates that the sound will be played rather than recorded
			args = dict(
				format = p.get_format_from_width(wf.getsampwidth()),
				channels = wf.getnchannels(),
				rate = wf.getframerate(),
				output = True
			)

			# Open PyAudio stream
			stream = p.open(**args)
		
			# Read wav data in chunks
			data = wf.readframes(chunk)

			# Get the total number of frames
			total_frames = wf.getnframes()

			# Calculate duration in seconds
			max_seconds = total_frames / float(wf.getframerate())

			remaining_data = lambda : wf.readframes(chunk)
		else:
			# Load the audio file
			audio = AudioSegment.from_file(path)

			# Convert to WAV format
			audio_data = BytesIO()
			audio.export(audio_data, format="wav")
			audio_data.seek(0)

			# Create an interface to PyAudio
			p = PyAudio()

			# 'output = True' indicates that the sound will be played rather than recorded
			args = dict(
				format=p.get_format_from_width(audio.sample_width),
				channels=audio.channels,
				rate=audio.frame_rate,
				output=True
			)

			# Open PyAudio stream
			stream = p.open(**args)

			# Read data
			data = audio_data.read(chunk)

			# Function to read remaining data
			remaining_data = lambda : audio_data.read(chunk)

			# Maximum duration of audio in seconds
			max_seconds = len(audio) / 1000

		# Convert duration to hours, minutes, and seconds
		max_secs = max_seconds % 60
		max_mins = max_seconds // 60
		max_hours = max_mins // 60

		max_duration = f"{int(max_hours):02d}:{int(max_mins):02d}:{int(max_secs):02d}"
		filename.config(text=file)
		duration.config(text="00:00:00 / 00:00:00")
		manage_widget(widgets=["progress", "filename", "duration"], statuses=[True, True, True])
		animate.set(True)
		
		# Record the start time
		start = time()

		# Play the sound by writing the audio data to the stream
		while len(data) > 0:
			# Check if a stop signal is received
			if window_alert.get() == "stop" or window_alert.get() == "break":
				break

			# Write audio data to stream
			stream.write(data)

			# Read next chunk of data
			data = remaining_data()

			# Calculate the duration of the playing
			seconds = time() - start
			secs = seconds % 60
			mins = seconds // 60
			hours = mins // 60

			if seconds >= max_seconds:
				seconds = max_seconds

			# if secs >= max_secs and max_mins == 0 and max_hours == 0:
			# 	secs = max_secs

			duration.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d} / {max_duration}")
			frame.coords(progress_bar, bar_len_x1, bar_len_y1, bar_len_x1+((bar_fill_length / 100) * ((seconds / max_seconds) * 100)), bar_len_y2+1)

		if not window_alert.get() == "break":
			animate.set(False)

		# Close and terminate the stream
		stream.close()
		p.terminate()

def record():
	# Create a PyAudio instance
	audio = PyAudio()

	# Open an audio stream with specified parameters
	stream = audio.open(format=paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

	# Initialize an empty list to store audio frames
	frames = []

	# Record the start time
	start = time()

	# Continuously read audio data from the stream while the recording flag is True
	while recording.get():
		# Read a chunk of audio data from the stream
		data = stream.read(1024)

		# Append the audio data to the frames list
		frames.append(data)

		# Calculate the duration of the recording
		end = time() - start
		secs = end % 60
		mins = end // 60
		hours = mins // 60

		duration.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}")
	
	# Close and terminate the stream
	stream.stop_stream()
	stream.close()
	audio.terminate()

	# Get the current date and time
	current_time = datetime.now()

	# Format the date and time into a string
	timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

	# Open a WAV file in write binary mode, using the timestamp in the filename
	sound_file = wave.open(f"{recording_save_path}/recording_{timestamp}.wav", "wb")
	
	# Set the number of channels to 1 (mono)
	sound_file.setnchannels(1)
	
	# Set the sample width based on the sample size of the audio data
	sound_file.setsampwidth(audio.get_sample_size(paInt16))

	# Set the frame rate to 44100 samples per second
	sound_file.setframerate(44100)

	# Write the audio frames to the WAV file by joining them into a single byte string
	sound_file.writeframes(b"".join(frames))

	# Close the WAV file
	sound_file.close()

	record_finish.set(True)

def add_recording():
	manage_widget(
		widgets=["mic", "filename", "duration", "progress"],
		statuses=[False, False, False, False]
		)
	
	window_alert.set("stop")
	recording.set(False)
	animate.set(False)
	root.update()
	
	path = filedialog.askopenfilename(
		title="Open a file",
		initialdir="recordings",
		filetypes=(
			("Audio files", "*.wav;*.mp3;*.flac;*.aac"),
			# ("All files", "*.*")
			)
		)
	
	file, ext = os.path.splitext(os.path.split(path)[-1])
	file = file[0:30].strip()+"..."+file[-10:]+ext
	
	window_alert.set(None)
	Thread(target=play_recording, args=(path, file, )).start()

def record_btn():
	if mic_btn.cget("text") == "◉":
		manage_widget(
			widgets=["mic", "duration", "progress"],
			statuses=[True, True, False]
			)

		window_alert.set("break")
		root.update()
		
		recording.set(True)
		animate.set(True)

		Thread(target=record).start()
	else:
		manage_widget(widgets=["mic", "filename", "duration"], statuses=[False, False, False])
		recording.set(False)
		animate.set(False)

animate = BooleanVar()
recording = BooleanVar()
record_finish = BooleanVar()
window_alert = StringVar()

def manage_widget(widgets, statuses):
	for widget, status in zip(widgets, statuses):
		if widget == "mic":
			if status:
				mic_btn.config(text="◼", fg="#da3c3c", activeforeground="#da3c3c")
			else:
				mic_btn.config(text="◉", fg="white", activeforeground="white")

		elif widget == "progress":
			if status:
				frame.itemconfig(progress_line, state="normal")
				frame.itemconfig(progress_bar, state="normal")
			else:
				frame.itemconfig(progress_line, state="hidden")
				frame.itemconfig(progress_bar, state="hidden")

		elif widget == "filename":
			if status:
				filename.place_configure(relx=0.5, rely=0.60, anchor='center')
			else:
				filename.place_forget()

		elif widget == "duration":
			if status:
				duration.place_configure(relx=0.5, rely=0.72, anchor='center')
			else:
				duration.place_forget()

window = Canvas(root, width=window_width, height=window_height)
window.create_image(100, 390, image=bg_image)
window.create_text(400, 35, text="Voice Recorder", fill="white", font=("Verdana", 22))
window.pack()

frame_width = 500
frame_height = 350

frame = Canvas(
	master=window,
	width=frame_width,
	height=frame_height,
	bg="#151515",
	# bd=0, highlightthickness=0, relief='ridge'
	)
frame.place(relx=0.5, rely=0.5, anchor="center")

mic = frame.create_image((frame_width/2), (frame_height/2)-40, image=mic_image)

bar_len_x1, bar_len_x2 = [166, 336]
bar_len_y1, bar_len_y2 = [235, 237]
bar_fill_length = (bar_len_x2 - bar_len_x1) + 0.6

progress_line = frame.create_rectangle(bar_len_x1, bar_len_y1, bar_len_x2, bar_len_y2, outline="white", fill="white", state="hidden")
progress_bar = frame.create_rectangle(bar_len_x1, bar_len_y1, bar_len_x1, bar_len_y2+1, outline="", fill="#884ef2", state="hidden")

filename = Label(frame, bg="#151515", fg="white", font=("Verdana", 10))
duration = Label(frame, bg="#151515", fg="white", font=("Verdana", 10))

window.create_rectangle(
	0, 460, 800, 462,
	fill="white",
	outline=""
	)

window.create_text(
	80, 480, fill="white",
	font=("Verdana", 10),
	text=f"Project by: {__author__}"
	)

window.create_text(
	740, 480, fill="white",
	font=("Verdana", 10),
	text=f"Version: {__version__}"
	)

btn_frame = Frame(frame, bg="#151515", highlightbackground="white", highlightthickness=1, pady=4, padx=4)
btn_frame.place(anchor="center", rely=0.85, relx=0.5)

open_btn = Button(
	btn_frame, cursor="hand2", text="+",
	command=add_recording, width=7,
	fg="white", bg="#5516c9",
	activeforeground="white",
	activebackground="#470eb1",
	border=0, font=("Verdana", 13, "bold")
	)

empty_space = Frame(btn_frame, bg="#151515")

mic_btn = Button(
	btn_frame, cursor="hand2", text="◉",
	command=record_btn, width=7,
	fg="white", bg="#5516c9",
	activeforeground="white",
	activebackground="#470eb1",
	border=0, font=("Verdana", 13)
	)

open_btn.grid(row=0, column=0)
empty_space.grid(row=0, column=1, padx=1)
mic_btn.grid(row=0, column=2)

update_root()
root.mainloop()
