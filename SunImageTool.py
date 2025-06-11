import flet as ft
from PIL import Image
import io
import base64
import datetime

def main(page: ft.Page):
    page.title = "Sunspot Levels Adjuster"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20

    # state holds both original and last adjusted images
    state = {"original": None, "adjusted": None}

    # Image display
    img_control = ft.Image(width=600)

    # Sliders (disabled until image is loaded)
    black_slider = ft.Slider(min=0, max=255, value=0, disabled=True)
    white_slider = ft.Slider(min=0, max=255, value=255, disabled=True)
    gamma_slider = ft.Slider(min=0.1, max=5.0, value=1.0, divisions=49, disabled=True)

    def update_image():
        img = state["original"]
        if img is None:
            return

        b = int(black_slider.value)
        wht = int(white_slider.value)
        g = float(gamma_slider.value)

        # build LUT
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
        full_lut = lut * 3

        # apply and store
        adjusted = img.point(full_lut)
        state["adjusted"] = adjusted

        # display
        buf = io.BytesIO()
        adjusted.save(buf, format="PNG")
        img_control.src_base64 = base64.b64encode(buf.getvalue()).decode()
        page.update()

    # handle file open
    def pick_files_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        file = e.files[0]
        # desktop: file.path, web: file.content
        if getattr(file, "path", None):
            img = Image.open(file.path).convert("RGB")
        else:
            img = Image.open(io.BytesIO(file.content)).convert("RGB")
        state["original"] = img

        # enable controls
        for ctr in (black_slider, white_slider, gamma_slider, export_button):
            ctr.disabled = False
        page.update()

        update_image()

    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)

    upload_button = ft.ElevatedButton(
        "Upload Photo",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda e: file_picker.pick_files(allow_multiple=False),
    )

    # Export button (disabled until first render)
    def export_image(e):
        img = state["adjusted"]
        if img is None:
            return
        fn = datetime.datetime.now().strftime("adjusted_%Y%m%d_%H%M%S.png")
        img.save(fn)
        page.snack_bar = ft.SnackBar(ft.Text(f"Saved to {fn}"))
        page.snack_bar.open = True
        page.update()

    export_button = ft.ElevatedButton(
        "Export Photo",
        icon=ft.Icons.FILE_DOWNLOAD,  # <-- corrected here
        on_click=export_image,
        disabled=True,
    )

    # slider callbacks
    def on_change_slider(e):
        update_image()

    black_slider.on_change = on_change_slider
    white_slider.on_change = on_change_slider
    gamma_slider.on_change = on_change_slider

    # layout
    page.add(
        ft.Column(
            [
                ft.Row([upload_button, export_button], alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=20),
                img_control,
                ft.Text("Adjust Levels to Increase Contrast", size=16, weight="bold"),
                # labeled sliders
                ft.Row(
                    [
                        ft.Column([ft.Text("Black Point"), black_slider]),
                        ft.Column([ft.Text("White Point"), white_slider]),
                        ft.Column([ft.Text("Gamma"), gamma_slider]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ],
            tight=True,
        )
    )

# launch as native desktop app
ft.app(target=main)
