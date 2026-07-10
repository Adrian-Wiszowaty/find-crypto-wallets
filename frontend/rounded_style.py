import tkinter as tk
import ttkbootstrap as ttk
from typing import Tuple, List, Optional, Any
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
                     outline: Optional[str] = None,
                     corners: Tuple[bool, bool, bool, bool] = (True, True, True, True)) -> Any:

        scale = 4
        size = radius * 2 + 4
        side = size * scale

        image = Image.new("RGB", (side, side), background)
        ImageDraw.Draw(image).rounded_rectangle(
            (0, 0, side - 1, side - 1), radius=radius * scale, fill=fill,
            outline=outline, width=scale if outline else 0, corners=corners)

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

        normal = RoundedStyle._rounded_image(base, background, radius, corners=corners)
        hover = RoundedStyle._rounded_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_HOVER_SHADE),
            background, radius, corners=corners)
        pressed = RoundedStyle._rounded_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_PRESSED_SHADE),
            background, radius, corners=corners)
        disabled = RoundedStyle._rounded_image(colors.get("light"), background, radius, corners=corners)

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
    def _date_button_image(fill: str, background: str,
                         corners: Tuple[bool, bool, bool, bool]) -> Any:

        scale = 4
        radius = GuiConstants.GUI_CORNER_RADIUS
        w, h = GuiConstants.GUI_DATE_BUTTON_SIZE
        side_w, side_h = w * scale, h * scale

        image = Image.new("RGB", (side_w, side_h), background)
        ImageDraw.Draw(image).rounded_rectangle((0, 0, side_w - 1, side_h - 1), radius=radius * scale,
                                              fill=fill, corners=corners)

        photo = ImageTk.PhotoImage(image.resize((w, h), Image.Resampling.LANCZOS))
        RoundedStyle._image_cache.append(photo)
        return photo

    @staticmethod
    def create_rounded_date_button_style(style_name: str, color_name: str,
                                       corners: Tuple[bool, bool, bool, bool] = (True, True, True, True)) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        base = colors.get(color_name)
        background = colors.bg

        normal = RoundedStyle._date_button_image(base, background, corners)
        hover = RoundedStyle._date_button_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_HOVER_SHADE), background, corners)
        pressed = RoundedStyle._date_button_image(
            RoundedStyle._shade_color(base, GuiConstants.GUI_BUTTON_PRESSED_SHADE), background, corners)
        disabled = RoundedStyle._date_button_image(colors.get("light"), background, corners)

        element = f"{style_name}.background"
        style.element_create(element, "image", normal,
                           ("disabled", disabled),
                           ("pressed", pressed),
                           ("active", hover),
                           border=0, padding=0, sticky="")
        style.layout(style_name, [(element, {"sticky": "nsew"})])
        style.configure(style_name, borderwidth=0, focuscolor="", padding=0)

    @staticmethod
    def create_rounded_field_style(style_name: str, widget_class: str, outline_color: str,
                                 corners: Tuple[bool, bool, bool, bool] = (True, True, True, True)) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        radius = GuiConstants.GUI_CORNER_RADIUS
        background = colors.bg
        fill = GuiConstants.GUI_FIELD_BG_COLOR

        normal = RoundedStyle._rounded_image(fill, background, radius, outline_color, corners)
        focused = RoundedStyle._rounded_image(fill, background, radius, colors.info, corners)
        disabled = RoundedStyle._rounded_image(colors.get("light"), background, radius, outline_color, corners)

        element = f"{style_name}.field"
        style.element_create(element, "image", normal,
                           ("disabled", disabled),
                           ("focus", focused),
                           border=radius, padding=0, sticky="nsew")

        inner: List[Any] = [(f"{widget_class}.padding", {"sticky": "nswe", "children": [
            (f"{widget_class}.textarea", {"sticky": "nswe"})]})]
        if widget_class == "Combobox":
            inner.insert(0, ("Combobox.downarrow", {"side": "right", "sticky": "ns"}))

        layout: Any = [(element, {"sticky": "nswe", "children": inner})]
        style.layout(style_name, layout)
        style.configure(style_name,
                       borderwidth=0,
                       padding=GuiConstants.GUI_FIELD_PADDING,
                       arrowcolor=colors.info,
                       foreground=colors.fg,
                       fieldbackground=fill,
                       background=background,
                       selectbackground=colors.info,
                       selectforeground=colors.selectfg)
        style.map(style_name, fieldbackground=[("readonly", fill)])

    @staticmethod
    def _panel_corner_tiles(fill: str, background: str, radius: int) -> List[Any]:

        scale = 4
        side = radius * 2 * scale

        image = Image.new("RGB", (side, side), background)
        ImageDraw.Draw(image).rounded_rectangle(
            (0, 0, side - 1, side - 1), radius=radius * scale, fill=fill)
        image = image.resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)

        return [image.crop((0, 0, radius, radius)),
                image.crop((radius, 0, radius * 2, radius)),
                image.crop((0, radius, radius, radius * 2)),
                image.crop((radius, radius, radius * 2, radius * 2))]

    @staticmethod
    def create_rounded_panel(parent: tk.Misc, fill: str, **text_options: Any) -> Tuple[Any, Any]:

        radius = GuiConstants.GUI_PANEL_RADIUS
        colors: Any = ttk.Style().colors
        background = colors.bg

        container = ttk.Frame(parent)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        backdrop = tk.Label(container, borderwidth=0, highlightthickness=0)
        backdrop.place(x=0, y=0, relwidth=1, relheight=1)

        text = tk.Text(container, borderwidth=0, highlightthickness=0, **text_options)
        text.grid(row=0, column=0, padx=radius, pady=radius, sticky="nsew")

        tiles = RoundedStyle._panel_corner_tiles(fill, background, radius)
        state: dict = {}

        def redraw(event: Any) -> None:
            size = (event.width, event.height)
            if size == state.get("size") or min(size) < radius * 2:
                return
            state["size"] = size

            image = Image.new("RGB", size, fill)
            image.paste(tiles[0], (0, 0))
            image.paste(tiles[1], (size[0] - radius, 0))
            image.paste(tiles[2], (0, size[1] - radius))
            image.paste(tiles[3], (size[0] - radius, size[1] - radius))

            photo = ImageTk.PhotoImage(image)
            backdrop.configure(image=photo)
            state["photo"] = photo

        container.bind("<Configure>", redraw)
        return container, text

    @staticmethod
    def configure_ttk_style() -> None:

        colors: Any = ttk.Style().colors

        RoundedStyle.create_rounded_button_style("Rounded.TButton", "primary")
        RoundedStyle.create_rounded_button_style("RoundedRun.TButton", "success")
        RoundedStyle.create_rounded_button_style("RoundedClose.TButton", "danger")
        RoundedStyle.create_rounded_date_button_style("RoundedDate.TButton", "info",
                                                    corners=(False, True, True, False))

        RoundedStyle.create_rounded_field_style("Rounded.TEntry", "Entry", colors.get("border"))
        RoundedStyle.create_rounded_field_style("Rounded.TCombobox", "Combobox", colors.info)
        RoundedStyle.create_rounded_field_style("RoundedDate.TEntry", "Entry", colors.info,
                                              corners=(True, False, False, True))
