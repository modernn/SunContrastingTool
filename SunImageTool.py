import flet as ft
from PIL import Image
import io
import base64

def main(page: ft.Page):
    page.title = "Sunspot Levels Adjuster"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20

    # state dict to hold the current original image
    state = {"original": None}

    # Image control
    img_control = ft.Image(width=600)

    # Sliders start disabled until an image is loaded
    black_slider = ft.Slider(
        min=0, max=255, value=0, label="Black Point: 0", disabled=True
    )
    white_slider = ft.Slider(
        min=0, max=255, value=255, label="White Point: 255", disabled=True
    )
    gamma_slider = ft.Slider(
        min=0.1,
        max=5.0,
        value=1.0,
        divisions=49,
        label="Gamma: 1.00",
        disabled=True,
    )

    def update_image():
        """Rebuild the LUT, apply to the loaded image, and refresh display."""
        img = state["original"]
        if img is None:
            return

        b = int(black_slider.value)
        wht = int(white_slider.value)
        g = float(gamma_slider.value)

        # single-channel LUT
        lut = []
        for i in range(256):
            if i <= b:
                lut.append(0)
            elif i >= wht:
                lut.append(255)
            else:
                x = (i - b) / (wht - b)
                y = x ** (1.0 / g)
                lut.append(int(y * 255 + 0.5))

        full_lut = lut * 3  # same for R, G, B
        adjusted = img.point(full_lut)

        # encode to base64 PNG
        buf = io.BytesIO()
        adjusted.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        img_control.src_base64 = b64
        page.update()

    # FilePicker and its result handler
    def pick_files_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        file = e.files[0]

        # --- FIX: handle desktop (file.path) vs. web (file.content) ---
        if getattr(file, "path", None):
            img = Image.open(file.path).convert("RGB")
        else:
            img = Image.open(io.BytesIO(file.content)).convert("RGB")
        # -------------------------------------------------------------

        state["original"] = img

        # enable sliders now that we have an image
        for s in (black_slider, white_slider, gamma_slider):
            s.disabled = False
        page.update()

        # initial render with defaults
        update_image()

    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)

    upload_button = ft.ElevatedButton(
        "Upload Photo",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda e: file_picker.pick_files(allow_multiple=False),
    )

    # wire up slider callbacks
    def on_black_change(e):
        black_slider.label = f"Black Point: {int(black_slider.value)}"
        page.update()
        update_image()

    def on_white_change(e):
        white_slider.label = f"White Point: {int(white_slider.value)}"
        page.update()
        update_image()

    def on_gamma_change(e):
        gamma_slider.label = f"Gamma: {gamma_slider.value:.2f}"
        page.update()
        update_image()

    black_slider.on_change = on_black_change
    white_slider.on_change = on_white_change
    gamma_slider.on_change = on_gamma_change

    # layout
    page.add(
        ft.Column(
            [
                upload_button,
                ft.Divider(height=20),
                img_control,
                ft.Text("Adjust Levels to Increase Contrast", size=16, weight="bold"),
                black_slider,
                white_slider,
                gamma_slider,
            ],
            tight=True,
        )
    )

# Launch as a native desktop app:
ft.app(target=main)
