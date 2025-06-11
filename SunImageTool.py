import flet as ft
from sunpy.map import Map
import astropy.units as u
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import io, base64, datetime, tempfile, os, math

# --- Helpers ---

def overlay_grid_pil(img: Image.Image) -> Image.Image:
    """Draw a compass and simple lat/lon grid on a PIL image."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    cx, cy = w/2, h/2
    r = min(cx, cy) * 0.95

    # Compass
    for angle, label in [(0,"N"), (90,"E"), (180,"S"), (270,"W")]:
        rad = math.radians(angle)
        ex = cx + r * math.sin(rad)
        ey = cy - r * math.cos(rad)
        draw.line([(cx,cy),(ex,ey)], fill=(255,255,0), width=2)
        lx = cx + (r+20)*math.sin(rad)
        ly = cy - (r+20)*math.cos(rad)
        draw.text((lx-5, ly-5), label, fill=(255,255,0))

    # Lat circles ±30°, ±60°
    for lat in [30, 60]:
        rr = r * math.cos(math.radians(lat))
        draw.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=(255,255,255), width=1)

    # Lon lines every 30°
    for lon in range(0,360,30):
        rad = math.radians(lon)
        x1 = cx + r*math.cos(rad)
        y1 = cy + r*math.sin(rad)
        x2 = cx - r*math.cos(rad)
        y2 = cy - r*math.sin(rad)
        draw.line([(x1,y1),(x2,y2)], fill=(255,255,255), width=1)

    return img

def map_to_pil(mp: Map) -> Image.Image:
    """Render a SunPy Map to a PIL image with limb + heliographic grid."""
    fig = plt.figure(figsize=(5,5), dpi=150)
    ax = fig.add_subplot(1,1,1, projection=mp)
    mp.plot(axes=ax)
    mp.draw_limb(axes=ax)
    mp.draw_grid(axes=ax, grid_spacing=15*u.deg, annotate=True, system='stonyhurst')
    ax.set_title(getattr(mp, "name","Sun"))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def apply_levels(img: Image.Image, b: int, wht: int, g: float) -> Image.Image:
    """Apply black/white/gamma LUT to a PIL image."""
    lut = []
    for i in range(256):
        if i <= b:
            lut.append(0)
        elif i >= wht:
            lut.append(255)
        else:
            x = (i-b)/(wht-b)
            y = x**(1.0/g)
            lut.append(int(y*255+0.5))
    full = lut*3
    return img.point(full)

def pil_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --- App ---

def main(page: ft.Page):
    page.title = "Sun Contrasting & Solar Viewer"
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.START

    # state slots for up to two images/maps
    state = {"img1": None, "img2": None}

    # Sliders for levels (disabled until first load)
    black_slider = ft.Slider(min=0, max=255, value=0, label="Black Point: 0", disabled=True)
    white_slider = ft.Slider(min=0, max=255, value=255, label="White Point: 255", disabled=True)
    gamma_slider = ft.Slider(min=0.1, max=5.0, divisions=49, value=1.0, label="Gamma: 1.00", disabled=True)

    # Image + pan/zoom
    img_ctrl = ft.Image(width=800)
    viewer = ft.InteractiveViewer(content=img_ctrl,
                                  pan_enabled=True,
                                  scale_enabled=True,
                                  min_scale=1.0,
                                  max_scale=5.0)

    # File pickers & buttons
    picker1 = ft.FilePicker(on_result=lambda e: pick(e, "img1", btn2))
    picker2 = ft.FilePicker(on_result=lambda e: pick(e, "img2", export_btn))
    page.overlay.extend([picker1, picker2])

    btn1 = ft.ElevatedButton("Load Primary Image", on_click=lambda e: picker1.pick_files(False))
    btn2 = ft.ElevatedButton("Load Comparison Image", disabled=True, on_click=lambda e: picker2.pick_files(False))
    export_btn = ft.ElevatedButton("Export View", disabled=True, on_click=lambda e: export_view())

    def pick(e: ft.FilePickerResultEvent, key: str, enable_btn):
        if not e.files: return
        f = e.files[0]
        path = getattr(f, "path", None)
        # write temp if web mode
        if path is None:
            suffix = os.path.splitext(f.name)[1] or ".jpg"
            tf = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            tf.write(f.content)
            tf.flush()
            path = tf.name

        # decide mode
        if path.lower().endswith((".fits",".fts",".fit")):
            mp = Map(path)
            state[key] = {"type":"map","data":mp}
        else:
            pil = Image.open(path).convert("RGB")
            state[key] = {"type":"pil","data":pil}

        # enable controls
        for w in (black_slider, white_slider, gamma_slider):
            w.disabled = False
        if enable_btn: enable_btn.disabled = False
        export_btn.disabled = False
        page.update()
        render()

    def render():
        imgs = []
        # get slider values
        b = int(black_slider.value)
        wht = int(white_slider.value)
        g = float(gamma_slider.value)
        # update labels
        black_slider.label = f"Black Point: {b}"
        white_slider.label = f"White Point: {wht}"
        gamma_slider.label = f"Gamma: {g:.2f}"

        for key in ("img1","img2"):
            slot = state[key]
            if not slot: continue
            if slot["type"] == "map":
                base = map_to_pil(slot["data"])
            else:
                base = slot["data"].copy()
            # apply levels to everything
            lev = apply_levels(base, b, wht, g)
            # overlay grid
            img = overlay_grid_pil(lev)
            imgs.append(img)

        if not imgs:
            return

        # compose side-by-side
        if len(imgs) == 1:
            combo = imgs[0]
        else:
            w_tot = sum(im.width for im in imgs)
            h_max = max(im.height for im in imgs)
            combo = Image.new("RGBA",(w_tot,h_max))
            x=0
            for im in imgs:
                combo.paste(im,(x,(h_max-im.height)//2))
                x+=im.width

        img_ctrl.src_base64 = pil_to_base64(combo)
        page.update()

    def export_view():
        data = base64.b64decode(img_ctrl.src_base64)
        fn = datetime.datetime.now().strftime("view_%Y%m%d_%H%M%S.png")
        with open(fn,"wb") as f: f.write(data)
        page.snack_bar = ft.SnackBar(ft.Text(f"Saved: {fn}"))
        page.snack_bar.open = True
        page.update()

    # wire sliders
    for s in (black_slider, white_slider, gamma_slider):
        s.on_change = lambda e: render()

    # layout
    controls = ft.Row([
        btn1, btn2, export_btn
    ], alignment=ft.MainAxisAlignment.START)
    sliders = ft.Row([
        ft.Column([ft.Text("Black"), black_slider]),
        ft.Column([ft.Text("White"), white_slider]),
        ft.Column([ft.Text("Gamma"), gamma_slider])
    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

    page.add(controls, ft.Divider(height=20), viewer, sliders)

# run as desktop app
ft.app(target=main)
