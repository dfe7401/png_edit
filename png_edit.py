#!/usr/bin/env python3
import sys, re, gi, cairo, math
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib, Pango

class GuiControl:
    def __init__(self, initialWidth, initialHeight, img1, img2, debug=False):
        self.image1ontop = True
        self.image2ontop = False
        self.initialWidth = initialWidth
        self.initialHeight = initialHeight
        self.image1 = img1
        self.image2 = img2
        self.final1 = None
        self.final2 = None
        self.popup = None
        self.entry = None
        self.popup_choice = "clip"
        self.resolution = img1.orig_width if img1.orig_width > img1.orig_height else img1.orig_height
        if img2:
            max = img2.orig_width if img2.orig_width > img2.orig_height else img2.orig_height
            if max > self.resolution:
                self.resolution = max
        self.resolution += 20
        if self.resolution < 2000:
            self.resolution = 2000
        self.debug = debug
        self.selection = "Rectangle"
        self.point1 = []
        self.point2 = []
        self.image1_choice = "on"
        self.image2_choice = "on"
        self.image1_zoom = "on"
        self.image2_zoom = "on"
        self.zoom_choices = [0.5 + i / 10 for i in range(26)]
        self.image1_zoom_level = 1.0
        self.image2_zoom_level = 1.0
        self.world1_anchor = [0, 0]
        self.world1_width_height = [img1.orig_width, img1.orig_height]
        if img2:
            self.world2_anchor = [0, 0]
            self.world2_width_height = [img2.orig_width, img2.orig_height]
        self.view_window_width_height = [0, 0]
        self.undo_list = []

    def __str__(self):
        s = ""
        s += "image1ontop is {}".format(self.image1ontop)
        s += "\nimage2ontop is {}".format(self.image2ontop)
        return s

class Image:
    def __init__(self, file_name):
        self.fileName = file_name
        self.image = cairo.ImageSurface.create_from_png(file_name)
        self.orig_width = self.image.get_width()
        self.orig_height = self.image.get_height()
        self.format = self.image.get_format()
    def __str__(self):
        s = "File is " + self.fileName 
        s += "\nwidth: {}".format(self.orig_width)
        s += "\nheight: {}".format(self.orig_height)
        if self.format == 0:
            s += "\nFormat is RGBA"
        else:
            s += "\nFormat is RGB"
        return s

def toggle_cb(button, ctl, choice):
    if choice == 1:
        ctl.image1ontop = True if button.get_active() else False
    if choice == 2:
        ctl.image2ontop = True if button.get_active() else False
    if choice == 3:
        ctl.selection = "Rectangle"
    if choice == 4:
        ctl.selection = "Oval"
    ctl.darea.queue_draw()
    #print(ctl)

def expose_cb(widget, ctx, ctl):
    ctl.darea.set_size_request(250, 250)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    if ctl.image2:
        if ctl.image1ontop:
            ctx.save()
            ctx.translate(ctl.world2_anchor[0], ctl.world2_anchor[1])
            ctx.scale(ctl.image2_zoom_level, ctl.image2_zoom_level)
            ctx.set_source_surface(ctl.final2)
            ctx.paint()
            ctx.restore()
            ctx.save()
            ctx.translate(ctl.world1_anchor[0], ctl.world1_anchor[1])
            ctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
            ctx.set_source_surface(ctl.final1)
            ctx.paint()
            ctx.restore()
        else:
            ctx.save()
            ctx.translate(ctl.world1_anchor[0], ctl.world1_anchor[1])
            ctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
            ctx.set_source_surface(ctl.final1)
            ctx.paint()
            ctx.restore()
            ctx.save()
            ctx.translate(ctl.world2_anchor[0], ctl.world2_anchor[1])
            ctx.scale(ctl.image2_zoom_level, ctl.image2_zoom_level)
            ctx.set_source_surface(ctl.final2)
            ctx.paint()
            ctx.restore()
    else:
        ctx.save()
        ctx.translate(ctl.world1_anchor[0], ctl.world1_anchor[1])
        ctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
        ctx.set_source_surface(ctl.final1)
        ctx.paint()
        ctx.restore()
    if ctl.point1:
        if ctl.point1[0] < ctl.point2[0]:
            smallx = ctl.point1[0]
            bigx = ctl.point2[0]
        else:
            smallx = ctl.point2[0]
            bigx = ctl.point1[0]
        if ctl.point1[1] < ctl.point2[1]:
            smally = ctl.point1[1]
            bigy = ctl.point2[1]
        else:
            smally = ctl.point2[1]
            bigy = ctl.point1[1]
        if bigx - smallx < 4 or bigy - smally < 4:
            pass
        else:
            ctx.save()
            ctx.set_source_rgb(1, 1, 1)
            if ctl.selection == "Rectangle":
                ctx.rectangle(smallx, smally, bigx - smallx, bigy - smally)
            else:
                draw_oval(ctx, smallx, smally, bigx - smallx, bigy - smally)
            ctx.stroke()
            ctx.restore()
        
    if not ctl.point1 and ctl.debug:
        img_fname = 'rectangle_13.png'
        img_size = ctl.resolution
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_size, img_size)
        imgctx = cairo.Context(img)
        imgctx.set_source_surface(ctx.get_target())
        imgctx.paint()
        img.write_to_png(img_fname)

def draw_oval(imgctx, small_x, small_y, width, height):
    cx = small_x + width/2
    cy = small_y + height/2
    if width < height:
        r = width/2
        scale_x = 1.0
        scale_y = height/width
    else:
        r = height/2
        scale_x = width/height
        scale_y = 1.0
    imgctx.save()
    imgctx.translate(cx, cy)
    imgctx.scale(scale_x, scale_y)
    imgctx.translate(-cx, -cy)
    imgctx.arc(cx, cy, r, 0, math.pi*2)
    imgctx.restore()
        
def fill_hbox1(hbox, ctl):
    button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Image 1 on top")
    hbox.pack_start(button1, False, False, 0)
    button1.connect("toggled", toggle_cb, ctl, 1)
    button2 = Gtk.RadioButton.new_from_widget(button1)
    button2.set_label("Image 2 on top")
    button2.connect("toggled", toggle_cb, ctl, 2)
    hbox.pack_start(button2, False, False, 0)
    label = Gtk.Label(label = "Selection:")
    hbox.pack_start(label, False, False, 5)
    button3 = Gtk.RadioButton.new_with_label_from_widget(None, "Rectangle")
    hbox.pack_start(button3, False, False, 0)
    button3.connect("toggled", toggle_cb, ctl, 3)
    button4 = Gtk.RadioButton.new_from_widget(button3)
    button4.set_label("Oval")
    button4.connect("toggled", toggle_cb, ctl, 4)
    hbox.pack_start(button4, False, False, 0)
    button_left = Gtk.Button.new_with_label("<")
    button_left.connect("clicked", move_cb, "left", ctl)
    hbox.pack_start(button_left, False, False, 6)
    button_right = Gtk.Button.new_with_label(">")
    button_right.connect("clicked", move_cb, "right", ctl)
    hbox.pack_start(button_right, False, False, 3)
    button_up = Gtk.Button.new_with_label("^")
    button_up.connect("clicked", move_cb, "up", ctl)
    hbox.pack_start(button_up, False, False, 3)
    button_down = Gtk.Button.new_with_label("v")
    button_down.connect("clicked", move_cb, "down", ctl)
    hbox.pack_start(button_down, False, False, 3)
    
def undo_move(target, ctl):
    clear_surface(ctl.final1)
    ctx = cairo.Context(ctl.final1)
    pattern1 = cairo.SurfacePattern(ctl.image1.image)
    ctx.set_source(pattern1)
    ctx.paint()
    if ctl.image2:
        clear_surface(ctl.final2)
        ctx = cairo.Context(ctl.final2)
        pattern2 = cairo.SurfacePattern(ctl.image2.image)
        ctx.set_source(pattern2)
        ctx.paint()
    for move in ctl.undo_list:
        if target in move:
            pass
        else:
            #replay operation
            tokens = move.split()
            x0, y0, width, height = tokens[-4:]
            shape = tokens[-5]
            image = tokens[-6]
            operation = tokens[-7]
            redraw_final(image, operation, shape, float(x0), float(y0), float(width), float(height), ctl)
            #print(tokens)
    ctl.darea.queue_draw()

def redraw_final(image, op, shape, x0, y0, width, height, ctl):
    if image == "image1":
        surface = ctl.final1
        scratch = ctl.scratch1
    else:
        surface = ctl.final2
        scratch = ctl.scratch2
    clear_surface(scratch)
    ctx_scratch = cairo.Context(scratch)
    ctx_scratch.set_source_surface(surface)
    ctx_scratch.paint()
    clear_surface(surface)
    ctx_final = cairo.Context(surface)
    if op == "clip":
        ctx_final.set_source_surface(scratch)
        if shape == "rectangle":
            ctx_final.rectangle(x0, y0, width, height)
        else:
            draw_oval(ctx_final, x0, y0, width, height)
        ctx_final.clip()
        ctx_final.paint()
        ctx_final.reset_clip()
    else:
        ctx_scratch.set_operator(cairo.OPERATOR_SOURCE)
        ctx_scratch.set_source_rgba(0, 0, 0, 0)
        if shape == "rectangle":
            ctx_scratch.rectangle(x0, y0, width, height)
        else:
            draw_oval(ctx_scratch, x0, y0, width, height)
        ctx_scratch.fill()
        ctx_final.set_source_surface(scratch)
        ctx_final.paint()
    
def delete_move_cb(widget, ctl):
    choice = ctl.undo_combo.get_active_text()
    new_undo_list = []
    combo_index = -1
    for idx, move in enumerate(ctl.undo_list):
        if choice in move:
            combo_index = idx
            undo_move(move, ctl)
        else:
            new_undo_list.append(move)
    if combo_index == -1:
        return
    ctl.undo_combo.remove(combo_index)
    ctl.undo_list = new_undo_list

def fill_h_ctlbox(hbox, ctl):
    button1 = Gtk.Button.new_with_label("Delete")
    button1.connect("clicked", delete_move_cb, ctl)
    hbox.pack_start(button1, False, False, 0)
    button2 = Gtk.Button.new_with_label("Undo List")
    hbox.pack_start(button2, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_entry_text_column(0)
    hbox.pack_start(combo, False, False, 0)
    ctl.undo_combo = combo
    label = Gtk.Label(label = "zoom/move choice")
    hbox.pack_start(label, False, False, 5)
    label = Gtk.Label(label = "top")
    hbox.pack_start(label, False, False, 5)
    check1 = Gtk.CheckButton()
    check1.connect("toggled", zoom_move_cb, "top", ctl)
    check1.set_active(True)
    hbox.pack_start(check1, False, False, 5)
    if ctl.image2:
        label = Gtk.Label(label = "bottom")
        hbox.pack_start(label, False, False, 5)
        check2 = Gtk.CheckButton()
        check2.connect("toggled", zoom_move_cb, "bottom", ctl)
        check2.set_active(True)
        hbox.pack_start(check2, False, False, 5)
    button_plus = Gtk.Button.new_with_label("+")
    button_plus.connect("clicked", zoom_in_cb, ctl)
    hbox.pack_start(button_plus, False, False, 3)
    button_minus = Gtk.Button.new_with_label("-")
    button_minus.connect("clicked", zoom_out_cb, ctl)
    hbox.pack_start(button_minus, False, False, 3)
    
def fill_hbox2(hbox, ctl):
    img_vbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
    hbox.pack_start(img_vbox, False, False, 0)
    drawing = Gtk.DrawingArea()
    ctl.darea = drawing
    connect_drawing_area_signals(ctl)
    drawing.set_size_request(ctl.initialWidth, ctl.initialHeight)
    hbox.pack_start(drawing, True, True, 0)
    name1 = "img1: " + ctl.image1.fileName
    label = Gtk.Label(label = name1)
    img_vbox.pack_start(label, False, False, 6)
    s = "  width: {}   ".format(ctl.image1.orig_width)
    label = Gtk.Label(label = s)
    img_vbox.pack_start(label, False, False, 2)
    s = "  height: {}   ".format(ctl.image1.orig_height)
    label = Gtk.Label(label = s)
    img_vbox.pack_start(label, False, False, 2)
    if ctl.image2 is not None:
        name2 = "img2: " + ctl.image2.fileName
        label = Gtk.Label(label = name2)
        img_vbox.pack_start(label, False, False, 6)
        s = "  width: {}   ".format(ctl.image2.orig_width)
        label = Gtk.Label(label = s)
        img_vbox.pack_start(label, False, False, 3)
        s = "  height: {}   ".format(ctl.image2.orig_height)
        label = Gtk.Label(label = s)
        img_vbox.pack_start(label, False, False, 3)

def configure_event_cb(widget, event, ctl):
    ctl.view_window_width_height = [widget.get_allocated_width(), widget.get_allocated_height()]
    if not ctl.final1:
        ctl.scratch1 = widget.get_window().create_similar_surface(cairo.CONTENT_COLOR_ALPHA, ctl.resolution, ctl.resolution)
        ctl.final1 = widget.get_window().create_similar_surface(cairo.CONTENT_COLOR_ALPHA, ctl.resolution, ctl.resolution)
        ctx = cairo.Context(ctl.final1)
        pattern1 = cairo.SurfacePattern(ctl.image1.image)
        ctx.set_source(pattern1)
        ctx.paint()
        if ctl.image2:
            ctl.scratch2 = widget.get_window().create_similar_surface(cairo.CONTENT_COLOR_ALPHA, ctl.resolution, ctl.resolution)
            ctl.final2 = widget.get_window().create_similar_surface(cairo.CONTENT_COLOR_ALPHA, ctl.resolution, ctl.resolution)
            ctx = cairo.Context(ctl.final2)
            pattern2 = cairo.SurfacePattern(ctl.image2.image)
            ctx.set_source(pattern2)
            ctx.paint()

def button_press_event_cb(widget, event, ctl):
    if event.button != Gdk.BUTTON_PRIMARY:
        return
    ctl.point1 = [event.x, event.y]
    #print("button pressed")

def motion_notify_event_cb(widget, event, ctl):
    if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
        return
    ctl.point2 = [event.x, event.y]
    ctl.darea.queue_draw()
    #print("button moved")

def fill_popup(popup, ctl):
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    popup.add(vbox)
    hbox1 = Gtk.Box()
    vbox.pack_start(hbox1, False, True, 0)
    label = Gtk.Label(label = "Name: ")
    hbox1.pack_start(label, False, False, 6)
    ctl.entry = Gtk.Entry()
    ctl.entry.set_text("Name please")
    ctl.entry.set_width_chars(25)
    hbox1.pack_start(ctl.entry, False, False, 0)
    hbox2 = Gtk.Box()
    vbox.pack_start(hbox2, False, True, 8)
    label = Gtk.Label(label = "Image choice: ")
    hbox2.pack_start(label, False, False, 6)
    check1 = Gtk.CheckButton()
    check1.connect("toggled", check_image_cb, 1, ctl)
    check1.set_active(True)
    label = Gtk.Label(label = "   img1")
    hbox2.pack_start(label, False, False, 0)
    hbox2.pack_start(check1, False, False, 0)
    if ctl.image2:
        check2 = Gtk.CheckButton()
        check2.connect("toggled", check_image_cb, 2, ctl)
        check2.set_active(True)
        label = Gtk.Label(label = "   img2")
        hbox2.pack_start(label, False, False, 0)
        hbox2.pack_start(check2, False, False, 4)
    hbox3 = Gtk.Box()
    vbox.pack_start(hbox3, False, True, 8)
    button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Clip region")
    button2 = Gtk.RadioButton.new_with_mnemonic_from_widget(button1, "Erase region")
    button3 = Gtk.RadioButton.new_with_mnemonic_from_widget(button1, "Save to file")
    button1.connect("toggled", get_choice_cb, 1, ctl)
    button2.connect("toggled", get_choice_cb, 2, ctl)
    button3.connect("toggled", get_choice_cb, 3, ctl)
    hbox3.pack_start(button1, False, False, 2)
    hbox3.pack_start(button2, False, False, 2)
    hbox3.pack_start(button3, False, False, 2)
    hbox4 = Gtk.Box()
    vbox.pack_start(hbox4, False, True, 0)
    button1 = Gtk.Button.new_with_label("Ok")
    button2 = Gtk.Button.new_with_label("Cancel")
    hbox4.pack_start(button1, False, False, 2)
    hbox4.pack_end(button2, False, False, 2)
    button1.connect("clicked", process_popup, ctl)
    button2.connect("clicked", destroy_popup, ctl)

def zoom_move_cb(button, choice, ctl):
    if choice == "top":
        if button.get_active():
            if ctl.image1ontop:
                ctl.image1_zoom = "on"
            else:
                ctl.image2_zoom = "on"
        else:
            if ctl.image1ontop:
                ctl.image1_zoom = "off"
            else:
                ctl.image2_zoom = "off"
    if choice == "bottom":
        if button.get_active():
            if ctl.image1ontop:
                ctl.image2_zoom = "on"
            else:
                ctl.image1_zoom = "on"
        else:
            if ctl.image1ontop:
                ctl.image2_zoom = "off"
            else:
                ctl.image1_zoom = "off"

def zoom_in_cb(widget, ctl):
    if ctl.image1_zoom == "on":
        orig_width = ctl.image1.orig_width
        orig_height = ctl.image1.orig_height
        i = ctl.zoom_choices.index(ctl.image1_zoom_level)
        if i == len(ctl.zoom_choices) - 1:
            choice = i
        else:
            choice = i + 1
        current_width = orig_width * ctl.zoom_choices[choice]
        current_height = orig_height * ctl.zoom_choices[choice]
        ctl.world1_width_height = [current_width, current_height]
        ctl.image1_zoom_level = ctl.zoom_choices[choice]
        window_center_x = ctl.view_window_width_height[0] / 2
        window_center_y = ctl.view_window_width_height[1] / 2
        distance_to_anchor_x = window_center_x - ctl.world1_anchor[0]
        distance_to_anchor_y = window_center_y - ctl.world1_anchor[1]
        distance_to_anchor_x *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
        distance_to_anchor_y *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
        ctl.world1_anchor[0] = window_center_x - distance_to_anchor_x
        ctl.world1_anchor[1] = window_center_y - distance_to_anchor_y
        #print("image1 zoom in anchor", ctl.world1_anchor, "size", ctl.world1_width_height)
    if ctl.image2:
        if ctl.image2_zoom == "on":
            orig_width = ctl.image2.orig_width
            orig_height = ctl.image2.orig_height
            i = ctl.zoom_choices.index(ctl.image2_zoom_level)
            if i == len(ctl.zoom_choices) - 1:
                choice = i
            else:
                choice = i + 1
            current_width = orig_width * ctl.zoom_choices[choice]
            current_height = orig_height * ctl.zoom_choices[choice]
            ctl.world2_width_height = [current_width, current_height]
            ctl.image2_zoom_level = ctl.zoom_choices[choice]
            window_center_x = ctl.view_window_width_height[0] / 2
            window_center_y = ctl.view_window_width_height[1] / 2
            distance_to_anchor_x = window_center_x - ctl.world2_anchor[0]
            distance_to_anchor_y = window_center_y - ctl.world2_anchor[1]
            distance_to_anchor_x *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
            distance_to_anchor_y *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
            ctl.world2_anchor[0] = window_center_x - distance_to_anchor_x
            ctl.world2_anchor[1] = window_center_y - distance_to_anchor_y
            #print("image2 zoom in anchor", ctl.world2_anchor, "size", ctl.world2_width_height)
    ctl.darea.queue_draw()

def zoom_out_cb(widget, ctl):
    if ctl.image1_zoom == "on":
        orig_width = ctl.image1.orig_width
        orig_height = ctl.image1.orig_height
        i = ctl.zoom_choices.index(ctl.image1_zoom_level)
        if i == 0:
            choice = i
        else:
            choice = i - 1
        current_width = orig_width * ctl.zoom_choices[choice]
        current_height = orig_height * ctl.zoom_choices[choice]
        ctl.world1_width_height = [current_width, current_height]
        ctl.image1_zoom_level = ctl.zoom_choices[choice]
        window_center_x = ctl.view_window_width_height[0] / 2
        window_center_y = ctl.view_window_width_height[1] / 2
        distance_to_anchor_x = window_center_x - ctl.world1_anchor[0]
        distance_to_anchor_y = window_center_y - ctl.world1_anchor[1]
        distance_to_anchor_x *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
        distance_to_anchor_y *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
        ctl.world1_anchor[0] = window_center_x - distance_to_anchor_x
        ctl.world1_anchor[1] = window_center_y - distance_to_anchor_y
        #print("image1 zoom out anchor", ctl.world1_anchor, "size", ctl.world1_width_height)
    if ctl.image2:
        if ctl.image2_zoom == "on":
            orig_width = ctl.image2.orig_width
            orig_height = ctl.image2.orig_height
            i = ctl.zoom_choices.index(ctl.image2_zoom_level)
            if i == 0:
                choice = i
            else:
                choice = i - 1
            current_width = orig_width * ctl.zoom_choices[choice]
            current_height = orig_height * ctl.zoom_choices[choice]
            ctl.world2_width_height = [current_width, current_height]
            ctl.image2_zoom_level = ctl.zoom_choices[choice]
            window_center_x = ctl.view_window_width_height[0] / 2
            window_center_y = ctl.view_window_width_height[1] / 2
            distance_to_anchor_x = window_center_x - ctl.world2_anchor[0]
            distance_to_anchor_y = window_center_y - ctl.world2_anchor[1]
            distance_to_anchor_x *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
            distance_to_anchor_y *= ctl.zoom_choices[choice] / ctl.zoom_choices[i]
            ctl.world2_anchor[0] = window_center_x - distance_to_anchor_x
            ctl.world2_anchor[1] = window_center_y - distance_to_anchor_y
            #print("image2 zoom out anchor", ctl.world2_anchor, "size", ctl.world2_width_height)
    ctl.darea.queue_draw()

def check_image_cb(button, num, ctl):
    if num == 1:
        if button.get_active():
            ctl.image1_choice = "on"
        else:
            ctl.image1_choice = "off"
        #print("image 1 the choice is", ctl.image1_choice)
    if num == 2:
        if button.get_active():
            ctl.image2_choice = "on"
        else:
            ctl.image2_choice = "off"
        #print("image 2 the choice is", ctl.image2_choice)

def get_choice_cb(button, num, ctl):
    if num == 1:
        if button.get_active():
            ctl.popup_choice = "clip"
    if num == 2:
        if button.get_active():
            ctl.popup_choice = "erase"
    if num == 3:
        if button.get_active():
            ctl.popup_choice = "save"

def clear_surface(surface):
    ctx = cairo.Context(surface)
    ctx.set_operator(cairo.OPERATOR_SOURCE)
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.paint()
    
def draw_oval(imgctx, small_x, small_y, width, height):
    if width < 0.001 or height < 0.001:
        return
    cx = small_x + width/2
    cy = small_y + height/2
    if width < height:
        r = width/2
        scale_x = 1.0
        scale_y = height/width
    else:
        r = height/2
        scale_x = width/height
        scale_y = 1.0
    imgctx.save()
    imgctx.translate(cx, cy)
    imgctx.scale(scale_x, scale_y)
    imgctx.translate(-cx, -cy)
    imgctx.arc(cx, cy, r, 0, math.pi*2)
    imgctx.restore()

def translate_2_img_location(choice, x0, y0, x1, y1, ctl):
    if choice == 1:
        distance_x = x0 - ctl.world1_anchor[0]
        distance_y = y0 - ctl.world1_anchor[1]
        x0 = distance_x / ctl.image1_zoom_level
        y0 = distance_y / ctl.image1_zoom_level
        distance_x = x1 - ctl.world1_anchor[0]
        distance_y = y1 - ctl.world1_anchor[1]
        x1 = distance_x / ctl.image1_zoom_level
        y1 = distance_y / ctl.image1_zoom_level
    if choice == 2:
        distance_x = x0 - ctl.world2_anchor[0]
        distance_y = y0 - ctl.world2_anchor[1]
        x0 = distance_x / ctl.image2_zoom_level
        y0 = distance_y / ctl.image2_zoom_level
        distance_x = x1 - ctl.world2_anchor[0]
        distance_y = y1 - ctl.world2_anchor[1]
        x1 = distance_x / ctl.image2_zoom_level
        y1 = distance_y / ctl.image2_zoom_level
    return (x0, y0, x1, y1)
    
def erase_surface(name, ctl, choice, x0, y0, x1, y1):
    x0, y0, x1, y1 = translate_2_img_location(choice, x0, y0, x1, y1, ctl)
    entry = "{} erase ".format(name)
    if choice == 1 and ctl.image1_choice == "on":
        entry += "image1 "
        clear_surface(ctl.scratch1)
        ctx_scratch = cairo.Context(ctl.scratch1)
        ctx_scratch.set_source_surface(ctl.final1)
        ctx_scratch.paint()
        ctx_scratch.set_operator(cairo.OPERATOR_SOURCE)
        ctx_scratch.set_source_rgba(0, 0, 0, 0)
        if ctl.selection == "Rectangle":
            combo_text = entry + "rectangle"
            entry += "rectangle {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            ctx_scratch.rectangle(x0, y0, x1 - x0, y1 - y0)
        else:
            combo_text = entry + "oval"
            entry += "oval {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            draw_oval(ctx_scratch, x0, y0, x1 - x0, y1 - y0)
        ctx_scratch.fill()
        clear_surface(ctl.final1)
        ctx_final = cairo.Context(ctl.final1)
        ctx_final.set_source_surface(ctl.scratch1)
        ctx_final.paint()
        ctl.undo_list.append(entry)
        ctl.undo_combo.append_text(combo_text)
    entry = "{} erase ".format(name)
    if choice == 2 and ctl.image2_choice == "on":
        entry += "image2 "
        clear_surface(ctl.scratch2)
        ctx_scratch = cairo.Context(ctl.scratch2)
        ctx_scratch.set_source_surface(ctl.final2)
        ctx_scratch.paint()
        ctx_scratch.set_operator(cairo.OPERATOR_SOURCE)
        ctx_scratch.set_source_rgba(0, 0, 0, 0)
        if ctl.selection == "Rectangle":
            combo_text = entry + "rectangle"
            entry += "rectangle {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            ctx_scratch.rectangle(x0, y0, x1 - x0, y1 - y0)
        else:
            combo_text = entry + "oval"
            entry += "oval {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            draw_oval(ctx_scratch, x0, y0, x1 - x0, y1 - y0)
        ctx_scratch.fill()
        clear_surface(ctl.final2)
        ctx_final = cairo.Context(ctl.final2)
        ctx_final.set_source_surface(ctl.scratch2)
        ctx_final.paint()
        ctl.undo_list.append(entry)
        ctl.undo_combo.append_text(combo_text)
    ctl.darea.queue_draw()

def clip_surface(name, ctl, choice, x0, y0, x1, y1):
    x0, y0, x1, y1 = translate_2_img_location(choice, x0, y0, x1, y1, ctl)
    entry = "{} clip ".format(name)
    if choice == 1 and ctl.image1_choice == "on":
        entry += "image1 "
        clear_surface(ctl.scratch1)
        ctx_scratch = cairo.Context(ctl.scratch1)
        ctx_scratch.set_source_surface(ctl.final1)
        ctx_scratch.paint()
        clear_surface(ctl.final1)
        ctx_final = cairo.Context(ctl.final1)
        ctx_final.set_source_surface(ctl.scratch1)
        if ctl.selection == "Rectangle":
            combo_text = entry + "rectangle"
            entry += "rectangle {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            ctx_final.rectangle(x0, y0, x1 - x0, y1 - y0)
        else:
            combo_text = entry + "oval"
            entry += "oval {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            draw_oval(ctx_final, x0, y0, x1 - x0, y1 - y0)
        ctx_final.clip()
        ctx_final.paint()
        ctx_final.reset_clip()
        ctl.undo_list.append(entry)
        ctl.undo_combo.append_text(combo_text)
    entry = "{} clip ".format(name)
    if choice == 2 and ctl.image2_choice == "on":
        entry += "image2 "
        clear_surface(ctl.scratch2)
        ctx_scratch = cairo.Context(ctl.scratch2)
        ctx_scratch.set_source_surface(ctl.final2)
        ctx_scratch.paint()
        clear_surface(ctl.final2)
        ctx_final = cairo.Context(ctl.final2)
        ctx_final.set_source_surface(ctl.scratch2)
        if ctl.selection == "Rectangle":
            combo_text = entry + "rectangle"
            entry += "rectangle {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            ctx_final.rectangle(x0, y0, x1 - x0, y1 - y0)
        else:
            combo_text = entry + "oval"
            entry += "oval {} {} {} {}".format(x0, y0, x1 - x0, y1 - y0)
            draw_oval(ctx_final, x0, y0, x1 - x0, y1 - y0)
        ctx_final.clip()
        ctx_final.paint()
        ctx_final.reset_clip()
        ctl.undo_list.append(entry)
        ctl.undo_combo.append_text(combo_text)
    ctl.darea.queue_draw()
            
def process_popup(widget, ctl):
    name = ctl.entry.get_text()
    #print("the name is", name)
    #print("the choice is", ctl.popup_choice)
    #print("point1 is", ctl.point1)
    #print("point2 is", ctl.point2)
    if ctl.point1[0] < ctl.point2[0]:
        smallx = ctl.point1[0]
        bigx = ctl.point2[0]
    else:
        smallx = ctl.point2[0]
        bigx = ctl.point1[0]
    if ctl.point1[1] < ctl.point2[1]:
        smally = ctl.point1[1]
        bigy = ctl.point2[1]
    else:
        smally = ctl.point2[1]
        bigy = ctl.point1[1]
    width = int(bigx - smallx)
    height = int(bigy - smally)
    if ctl.popup_choice == "clip":
        #print("doing clip")
        clip_surface(name, ctl, 1, smallx, smally, bigx, bigy)
        if ctl.final2:
            clip_surface(name, ctl, 2, smallx, smally, bigx, bigy)
    if ctl.popup_choice == "erase":
        #print("doing erase")
        erase_surface(name, ctl, 1, smallx, smally, bigx, bigy)
        if ctl.final2:
            erase_surface(name, ctl, 2, smallx, smally, bigx, bigy)
    if ctl.debug:
        lst = [1,2] if ctl.final2 else [1]
        for i in lst:
            img_fname = 'layer{}.png'.format(i)
            img = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            imgctx = cairo.Context(img)
            if i == 1:
                imgctx.translate(ctl.world1_anchor[0], ctl.world1_anchor[1])
                imgctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
                imgctx.translate(smallx, smally)
                imgctx.set_source_surface(ctl.final1)
            else:
                imgctx.translate(ctl.world2_anchor[0], ctl.world2_anchor[1])
                imgctx.scale(ctl.image2_zoom_level, ctl.image2_zoom_level)
                imgctx.translate(smallx, smally)
                imgctx.set_source_surface(ctl.final2, -smallx, -smally)
            imgctx.paint()
            img.write_to_png(img_fname)
            #print(img_fname, "created")
    if ctl.popup_choice == "save":
        img_fname = name + ".png"
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        imgctx = cairo.Context(img)
        if not ctl.final2:
            offset_x = ctl.world1_anchor[0] - int(smallx)
            offset_y = ctl.world1_anchor[1] - int(smally)
            imgctx.save()
            imgctx.translate(offset_x, offset_y)
            imgctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
            imgctx.set_source_surface(ctl.final1)
            imgctx.paint()
            imgctx.restore()
        else:
            if ctl.image1ontop:
                offset_x = ctl.world2_anchor[0] - int(smallx)
                offset_y = ctl.world2_anchor[1] - int(smally)
                imgctx.save()
                imgctx.translate(offset_x, offset_y)
                imgctx.scale(ctl.image2_zoom_level, ctl.image2_zoom_level)
                imgctx.set_source_surface(ctl.final2)
                imgctx.paint()
                imgctx.restore()
                offset_x = ctl.world1_anchor[0] - int(smallx)
                offset_y = ctl.world1_anchor[1] - int(smally)
                imgctx.save()
                imgctx.translate(offset_x, offset_y)
                imgctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
                imgctx.set_source_surface(ctl.final1)
                imgctx.paint()
                imgctx.restore()
            else:
                offset_x = ctl.world1_anchor[0] - int(smallx)
                offset_y = ctl.world1_anchor[1] - int(smally)
                imgctx.save()
                imgctx.translate(offset_x, offset_y)
                imgctx.scale(ctl.image1_zoom_level, ctl.image1_zoom_level)
                imgctx.set_source_surface(ctl.final1)
                imgctx.paint()
                imgctx.restore()
                offset_x = ctl.world2_anchor[0] - int(smallx)
                offset_y = ctl.world2_anchor[1] - int(smally)
                imgctx.save()
                imgctx.translate(offset_x, offset_y)
                imgctx.scale(ctl.image2_zoom_level, ctl.image2_zoom_level)
                imgctx.set_source_surface(ctl.final2)
                imgctx.paint()
                imgctx.restore()
        img.write_to_png(img_fname)
    destroy_popup(widget, ctl)
    
def destroy_popup(widget, ctl):
    ctl.point1 = []
    ctl.popup.destroy()
    ctl.popup_choice = "clip"
    ctl.image1_choice = "on"
    ctl.image2_choice = "on"
    ctl.darea.queue_draw()
    
def button_release_event_cb(widget, event, ctl):
    if event.button != Gdk.BUTTON_PRIMARY:
        return
    ctl.point2 = [event.x, event.y]
    if abs(ctl.point1[0] - ctl.point2[0]) < 4 or abs(ctl.point1[1] - ctl.point2[1]) < 4:
        ctl.point1 = []
        return
    ctl.popup = Gtk.Window()
    fill_popup(ctl.popup, ctl)
    ctl.popup.set_title("Selection")
    ctl.popup.show_all()
    
def connect_drawing_area_signals(ctl):
    ctl.darea.connect("configure-event", configure_event_cb, ctl)
    ctl.darea.connect("draw", expose_cb, ctl)
    ctl.darea.connect("button-press-event", button_press_event_cb, ctl)
    ctl.darea.connect("motion-notify-event", motion_notify_event_cb, ctl)
    ctl.darea.connect("button-release-event", button_release_event_cb, ctl)
    ctl.darea.set_events(Gdk.EventMask.ALL_EVENTS_MASK)

    
class MyGtk(Gtk.Window):
    def __init__(self, img1, img2):
        super().__init__(title="png_edit")
        self.img1 = img1
        self.img2 = img2
        #self.ctl = GuiControl(400, 400, img1, img2)
        self.ctl = GuiControl(400, 400, img1, img2, True)
        self.connect("destroy", Gtk.main_quit)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        hbox1 = Gtk.Box()
        fill_hbox1(hbox1, self.ctl)
        vbox.pack_start(hbox1, False, True, 0)

        h_ctlbox = Gtk.Box()
        fill_h_ctlbox(h_ctlbox, self.ctl)
        vbox.pack_start(h_ctlbox, False, True, 0)
        
        hbox2 = Gtk.Box()
        fill_hbox2(hbox2, self.ctl)
        vbox.pack_start(hbox2, True, True, 0)
        #self.connect("key-press-event", key_press_event_cb, self.ctl)

def move_cb(widget, move, ctl):
    if move == "right":
        if ctl.image1_zoom == "on":
            ctl.world1_anchor[0] += 4
        if ctl.image2 and ctl.image2_zoom == "on":
            ctl.world2_anchor[0] += 4
    elif move == "left":
        if ctl.image1_zoom == "on":
            ctl.world1_anchor[0] -= 4
        if ctl.image2 and ctl.image2_zoom == "on":
            ctl.world2_anchor[0] -= 4
    elif move == "up":
        if ctl.image1_zoom == "on":
            ctl.world1_anchor[1] -= 4
        if ctl.image2 and ctl.image2_zoom == "on":
            ctl.world2_anchor[1] -= 4
    elif move == "down":
        if ctl.image1_zoom == "on":
            ctl.world1_anchor[1] += 4
        if ctl.image2 and ctl.image2_zoom == "on":
            ctl.world2_anchor[1] += 4
    else:
        pass
    ctl.darea.queue_draw()        

def run(file_list):
    if (len(file_list) > 2 or len(file_list) < 1):
        print("please provide 1 or 2 png files")
        return
    #print(file_list)
    image1 = Image(file_list[0])
    #printimage1)
    if len(file_list) == 2:
        image2 = Image(file_list[1])
        #print(image2)
    else:
        image2 = None
    mygtk = MyGtk(image1, image2)
    mygtk.show_all()
    Gtk.main()

if __name__ == "__main__":
    run(sys.argv[1:])
