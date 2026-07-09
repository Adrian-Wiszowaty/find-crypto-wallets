import ttkbootstrap as ttk
from typing import Tuple, List, Any
from PIL import Image, ImageDraw, ImageTk

from shared.constants.gui_constants import GuiConstants

class RoundedStyle:

    _image_cache: List[Any] = []

    @staticmethod
    def _shade_color(color: str, factor: float) -> str:

        channels = color.lstrip("#")
        r, g, b = (int(channels[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _rounded_image(fill: str, background: str, radius: int,
                     corners: Tuple[bool, bool, bool, bool] = (True, True, True, True)) -> Any:

        scale = 4
        size = radius * 2 + 4
        side = size * scale

        image = Image.new("RGB", (side, side), background)
        ImageDraw.Draw(image).rounded_rectangle(
            (0, 0, side - 1, side - 1), radius=radius * scale, fill=fill, corners=corners)

        photo = ImageTk.PhotoImage(image.resize((size, size), Image.Resampling.LANCZOS))
        RoundedStyle._image_cache.append(photo)
        return photo

    @staticmethod
    def create_rounded_button_style(style_name: str, color_name: str,
                                  corners: Tuple[bool, bool, bool, bool] = (True, True, True, True),
                                  padding: Any = GuiConstants.GUI_BUTTON_PADDING) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        base = colors.get(color_name)
        radius = GuiConstants.GUI_CORNER_RADIUS
        background = colors.bg

        normal = RoundedStyle._rounded_image(base, background, radius, corners)
        hover = RoundedStyle._rounded_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_HOVER_SHADE), background, radius, corners)
        pressed = RoundedStyle._rounded_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_PRESSED_SHADE), background, radius, corners)
        disabled = RoundedStyle._rounded_image(colors.get("light"), background, radius, corners)

        element = f"{style_name}.background"
        style.element_create(element, "image", normal,
                           ("disabled", disabled),
                           ("pressed", pressed),
                           ("active", hover),
                           border=radius, padding=0, sticky="nsew")
        style.layout(style_name, [
            (element, {"sticky": "nsew", "children": [
                ("Button.padding", {"sticky": "nsew", "children": [
                    ("Button.label", {"sticky": "nsew"})]})]})])
        style.configure(style_name,
                       foreground=colors.selectfg,
                       background=background,
                       borderwidth=0,
                       focuscolor="",
                       anchor="center",
                       padding=padding)
        style.map(style_name, foreground=[("disabled", colors.secondary)])

    @staticmethod
    def configure_ttk_style() -> None:

        RoundedStyle.create_rounded_button_style("Rounded.TButton", "primary")
        RoundedStyle.create_rounded_button_style("RoundedRun.TButton", "success")
        RoundedStyle.create_rounded_button_style("RoundedClose.TButton", "danger")
