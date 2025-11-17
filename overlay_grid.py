import tkinter as tk

root = tk.Tk()
root.title("Screen Grid")
root.attributes("-alpha", 0.25)       # transparency
root.attributes("-topmost", True)     # stay on top
root.overrideredirect(True)           # remove window border

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f"{screen_w}x{screen_h}+0+0")

canvas = tk.Canvas(root, width=screen_w, height=screen_h, highlightthickness=0)
canvas.pack()

# draw grid every 100 pixels
for x in range(0, screen_w, 100):
    canvas.create_line(x, 0, x, screen_h, fill="red")

for y in range(0, screen_h, 100):
    canvas.create_line(0, y, screen_w, y, fill="red")

# close overlay on ESC
def close(event):
    root.destroy()

root.bind("<Escape>", close)

root.mainloop()