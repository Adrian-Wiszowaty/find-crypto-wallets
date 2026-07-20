import tkinter as tk
import ttkbootstrap as ttk
from typing import Tuple, List, Optional, Any
from PIL import Image, ImageDraw, ImageTk

from shared.constants.gui_constants import GuiConstants

class RoundedStyle:

    _image_cache: List[Any] = []
    _date_picker_patched = False

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
    def create_rounded_button_style(style_name: str, color: str,
                                  corners: Tuple[bool, bool, bool, bool] = (True, True, True, True),
                                  padding: Any = GuiConstants.GUI_BUTTON_PADDING) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        base = color
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
    def _draw_calendar_glyph(draw: Any, box: Tuple[float, float, float, float], color: str) -> None:

        x0, y0, x1, y1 = box
        sx, sy = (x1 - x0) / 210, (y1 - y0) / 220

        def px(v: float) -> float: return x0 + v * sx
        def py(v: float) -> float: return y0 + v * sy

        draw.rounded_rectangle(
            [px(10), py(30), px(200), py(210)],
            radius=20 * min(sx, sy), outline=color, width=max(1, round(10 * min(sx, sy))))

        dots = [
            [40, 10, 50, 50], [100, 10, 110, 50], [160, 10, 170, 50],
            [70, 90, 90, 110], [110, 90, 130, 110], [150, 90, 170, 110],
            [30, 130, 50, 150], [70, 130, 90, 150], [110, 130, 130, 150], [150, 130, 170, 150],
            [30, 170, 50, 190], [70, 170, 90, 190], [110, 170, 130, 190]]
        for a, b, c, d in dots:
            draw.rectangle([px(a), py(b), px(c), py(d)], fill=color)

    @staticmethod
    def _date_button_image(fill: str, background: str, icon_color: str,
                         corners: Tuple[bool, bool, bool, bool]) -> Any:

        scale = 4
        radius = GuiConstants.GUI_CORNER_RADIUS
        w, h = GuiConstants.GUI_DATE_BUTTON_SIZE
        side_w, side_h = w * scale, h * scale

        image = Image.new("RGB", (side_w, side_h), background)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, side_w - 1, side_h - 1), radius=radius * scale,
                             fill=fill, corners=corners)

        margin_x, margin_y = side_w * 0.27, side_h * 0.25
        RoundedStyle._draw_calendar_glyph(
            draw, (margin_x, margin_y, side_w - margin_x, side_h - margin_y), icon_color)

        photo = ImageTk.PhotoImage(image.resize((w, h), Image.Resampling.LANCZOS))
        RoundedStyle._image_cache.append(photo)
        return photo

    @staticmethod
    def create_rounded_date_button_style(style_name: str, color: str,
                                       corners: Tuple[bool, bool, bool, bool] = (True, True, True, True)) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        background = colors.bg
        icon_color = colors.selectfg

        normal = RoundedStyle._date_button_image(color, background, icon_color, corners)
        hover = RoundedStyle._date_button_image(
            RoundedStyle._shade_color(color, GuiConstants.GUI_BUTTON_HOVER_SHADE), background, icon_color, corners)
        pressed = RoundedStyle._date_button_image(
            RoundedStyle._shade_color(color, GuiConstants.GUI_BUTTON_PRESSED_SHADE), background, icon_color, corners)
        disabled = RoundedStyle._date_button_image(colors.get("light"), background, colors.secondary, corners)

        element = f"{style_name}.background"
        style.element_create(element, "image", normal,
                           ("disabled", disabled),
                           ("pressed", pressed),
                           ("active", hover),
                           border=0, padding=0, sticky="")
        style.layout(style_name, [(element, {"sticky": "nsew"})])
        style.configure(style_name, borderwidth=0, focuscolor="", padding=0)

    @staticmethod
    def _arrow_image(color: str) -> Any:

        scale = 4
        w, h = GuiConstants.GUI_ARROW_SIZE
        side_w, side_h = w * scale, h * scale

        image = Image.new("RGBA", (side_w, side_h), (0, 0, 0, 0))
        cx, cy = side_w / 2, side_h / 2
        tri_w, tri_h = side_w * 0.5, side_h * 0.3
        ImageDraw.Draw(image).polygon([
            (cx - tri_w / 2, cy - tri_h / 2),
            (cx + tri_w / 2, cy - tri_h / 2),
            (cx, cy + tri_h / 2)], fill=color)

        photo = ImageTk.PhotoImage(image.resize((w, h), Image.Resampling.LANCZOS))
        RoundedStyle._image_cache.append(photo)
        return photo

    @staticmethod
    def create_rounded_field_style(style_name: str, widget_class: str, outline_color: str,
                                 corners: Tuple[bool, bool, bool, bool] = (True, True, True, True),
                                 focus_color: Optional[str] = None,
                                 arrow_color: Optional[str] = None) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        radius = GuiConstants.GUI_CORNER_RADIUS
        background = colors.bg
        fill = GuiConstants.GUI_FIELD_BG_COLOR
        focus_color = focus_color or colors.info

        normal = RoundedStyle._rounded_image(fill, background, radius, outline_color, corners)
        focused = RoundedStyle._rounded_image(fill, background, radius, focus_color, corners)
        disabled = RoundedStyle._rounded_image(colors.get("light"), background, radius, outline_color, corners)

        element = f"{style_name}.field"
        style.element_create(element, "image", normal,
                           ("disabled", disabled),
                           ("focus", focused),
                           border=radius, padding=0, sticky="nsew")

        inner: List[Any] = [(f"{widget_class}.padding", {"sticky": "nswe", "children": [
            (f"{widget_class}.textarea", {"sticky": "nswe"})]})]
        if widget_class == "Combobox":
            arrow_fill = arrow_color or colors.info
            arrow_element = f"{style_name}.downarrow"
            style.element_create(arrow_element, "image", RoundedStyle._arrow_image(arrow_fill), sticky="")
            inner.insert(0, (arrow_element, {"side": "right", "sticky": "ns"}))

        layout: Any = [(element, {"sticky": "nswe", "children": inner})]
        style.layout(style_name, layout)
        style.configure(style_name,
                       borderwidth=0,
                       padding=GuiConstants.GUI_FIELD_PADDING,
                       arrowcolor=arrow_color or colors.info,
                       foreground=colors.fg,
                       fieldbackground=fill,
                       background=background,
                       selectbackground=focus_color,
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
    def patch_date_picker_positioning() -> None:

        if RoundedStyle._date_picker_patched:
            return
        RoundedStyle._date_picker_patched = True

        from ttkbootstrap.dialogs.datepicker import DatePickerDialog

        original_setup_calendar = DatePickerDialog._setup_calendar

        def patched_setup_calendar(self: Any) -> None:
            real_deiconify = self.root.deiconify
            self.root.deiconify = lambda: None
            try:
                original_setup_calendar(self)
            finally:
                self.root.deiconify = real_deiconify
            self.root.deiconify()

        DatePickerDialog._setup_calendar = patched_setup_calendar

    @staticmethod
    def create_rounded_scrollbar_style(style_name: str) -> None:

        style = ttk.Style()
        colors: Any = style.colors
        radius = GuiConstants.GUI_SCROLLBAR_RADIUS
        trough = colors.get("light")

        normal = RoundedStyle._rounded_image(colors.secondary, trough, radius)
        active = RoundedStyle._rounded_image(
            RoundedStyle._shade_color(colors.secondary, GuiConstants.GUI_BUTTON_PRESSED_SHADE), trough, radius)

        thumb = f"{style_name}.thumb"
        style.element_create(thumb, "image", normal,
                           ("pressed", active), ("active", active),
                           border=radius, padding=0, sticky="nswe")

        layout: Any = [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            (thumb, {"sticky": "nswe", "expand": True})]})]
        style.layout(style_name, layout)
        style.configure(style_name, troughcolor=trough, borderwidth=0,
                       arrowsize=0, gripcount=0, width=GuiConstants.GUI_SCROLLBAR_WIDTH)

    @staticmethod
    def style_combobox_popdown(combobox: ttk.Combobox, scrollbar_style: str) -> None:

        colors: Any = ttk.Style().colors
        fill = GuiConstants.GUI_FIELD_BG_COLOR

        popdown = combobox.tk.eval(f"ttk::combobox::PopdownWindow {combobox}")
        combobox.tk.call(f"{popdown}.f.l", "configure",
                       "-background", fill,
                       "-foreground", colors.fg,
                       "-selectbackground", colors.secondary,
                       "-selectforeground", colors.selectfg,
                       "-borderwidth", 0,
                       "-highlightthickness", 1,
                       "-highlightbackground", colors.get("border"),
                       "-highlightcolor", colors.secondary,
                       "-relief", "flat")
        combobox.tk.call(f"{popdown}.f.sb", "configure", "-style", scrollbar_style)

    @staticmethod
    def configure_ttk_style() -> None:

        colors: Any = ttk.Style().colors

        RoundedStyle.patch_date_picker_positioning()

        RoundedStyle.create_rounded_button_style("Rounded.TButton", GuiConstants.GUI_ACCENT_COLOR)
        RoundedStyle.create_rounded_button_style("RoundedRun.TButton", colors.get("success"))
        RoundedStyle.create_rounded_button_style("RoundedClose.TButton", colors.get("danger"))
        RoundedStyle.create_rounded_date_button_style("RoundedDate.TButton", GuiConstants.GUI_ACCENT_COLOR,
                                                    corners=(False, True, True, False))

        RoundedStyle.create_rounded_field_style("Rounded.TEntry", "Entry", GuiConstants.GUI_ACCENT_COLOR,
                                              focus_color=GuiConstants.GUI_ACCENT_DEEP_COLOR)
        RoundedStyle.create_rounded_field_style("Rounded.TCombobox", "Combobox", GuiConstants.GUI_ACCENT_COLOR,
                                              focus_color=GuiConstants.GUI_ACCENT_DEEP_COLOR,
                                              arrow_color=GuiConstants.GUI_ACCENT_COLOR)
        RoundedStyle.create_rounded_field_style("RoundedDate.TEntry", "Entry", GuiConstants.GUI_ACCENT_COLOR,
                                              corners=(True, False, False, True),
                                              focus_color=GuiConstants.GUI_ACCENT_DEEP_COLOR)

        RoundedStyle.create_rounded_scrollbar_style("Rounded.Vertical.TScrollbar")
