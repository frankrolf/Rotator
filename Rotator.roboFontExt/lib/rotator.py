# menuTitle: Rotator

import ezui
from AppKit import NSColor
from lib.tools.misc import NSColorToRgba
from fontTools.pens.cocoaPen import CocoaPen
from fontTools.misc.roundTools import otRound
from lib.UI.integerEditText import NumberEditText
from mojo.UI import getDefault, UpdateCurrentGlyphView, CurrentGlyphWindow

from mojo.extensions import (
    getExtensionDefault, setExtensionDefault,
    getExtensionDefaultColor, setExtensionDefaultColor)
from vanilla import (
    Button, CheckBox, ColorWell, EditText,
    FloatingWindow, HorizontalLine, TextBox)

import merz
from merz.tools.drawingTools import NSImageDrawingTools
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
from mojo.events import getActiveEventTool


EXTENSION_KEY = 'de.frgr.rotator'

def rotator_symbol_factory(
        position=(0,0),
        width=20,
        strokeColor=(1, 0, 0, 1),
        strokeWidth=1
        ):
    bot = NSImageDrawingTools((width, width))

    pen = bot.BezierPath()
    pen.moveTo((width/2, 0))
    pen.lineTo((width/2, width))
    pen.closePath()

    pen2 = bot.BezierPath()
    pen2.moveTo((0, width/2))
    pen2.lineTo((width, width/2))
    pen2.closePath()

    bot.fill(None)
    bot.stroke(*strokeColor)
    bot.strokeWidth(strokeWidth)
    bot.drawPath(pen)
    bot.drawPath(pen2)
    bot.oval(width/4,width/4,width/2,width/2)
    
    return bot.getImage()
    
merz.SymbolImageVendor.registerImageFactory("rotator.circleCrosshair", rotator_symbol_factory)


def disable():
    return False
def enable():
    return True    

def nice_angle_string(angle):
    angle_result_string = u'%.2f' % angle
    if angle_result_string.endswith('.00'):
        angle_result_string = angle_result_string[0:-3]
    return u'%s°' % angle_result_string

def round_integer(value):
    """Same as int(), but accepts None."""
    if value is None:
        return None
    return otRound(value)
    
def is_near(coords, check_coords, tol=5):
    # Account for glyph editor zoom level when determining click hitbox
    sc_tol = tol * (1/CurrentGlyphWindow().getGlyphViewScale())
    if check_coords[0] - sc_tol < coords[0] < check_coords[0] + sc_tol and check_coords[1] - sc_tol < coords[1] < check_coords[1] + sc_tol:
        return True
    return False


class Rotator(Subscriber, ezui.WindowController):


    def build(self):

        content = """
        = TwoColumnForm
        
        : Steps:
        [_ _]              @stepsField
        
        ---
        
        : Origin:
        * HorizontalStack  @xyStack
        > [_ _]            @xField
        > [_ _]            @yField
        
        * HorizontalStack                          @alignmentStack
        > ({square.grid.3x3.bottommiddle.filled})  @alignBottomButton
        > ({square.grid.3x3.topmiddle.filled})     @alignTopButton
        > ({square.grid.3x3.middleleft.filled})    @alignLeftButton
        > ({square.grid.3x3.middleright.filled})   @alignRightButton

        ---
        
        : Color:
        * ColorWell        @strokeColorWell
        
        ---
        
        :
        [ ] Round points   @roundPointsCheckbox
        
        :
        (Apply)            @applyButton
        """
        
        column_1_width = 50
        column_2_width = 118
        field_width = 40
        symbol_config = {
            'scale'        : 'large', 
            'weight'       : 'light', 
            'renderingMode': 'hierarchical',
            }
        descriptionData = dict(
            content=dict(
                titleColumnWidth=column_1_width,
                itemColumnWidth=column_2_width
                ),
            xyStack=dict(
                distribution="gravity",
                ),
            alignmentStack=dict(
                height=15,
                distribution="equalSpacing",
                ),
            alignBottomButton=dict(
                symbolConfiguration=symbol_config
                ),
            alignTopButton=dict(
                symbolConfiguration=symbol_config
                ),
            alignLeftButton=dict(
                symbolConfiguration=symbol_config
                ),
            alignRightButton=dict(
                symbolConfiguration=symbol_config
                ),
            stepsField=dict(
                value=5,
                valueWidth=field_width,
                valueType='integer',
                valueIncrement=1,
                trailingText="0°",
                ),
            xField=dict(
                value=0,
                valueWidth=field_width,
                valueType='integer',
                valueIncrement=1,
                trailingText="X",
                ),
            yField=dict(
                value=0,
                valueWidth=field_width,
                valueType='integer',
                valueIncrement=1,
                trailingText="Y",
                ),
            roundPointsCheckbox=dict(
                value=True,
                ),
            strokeColorWell=dict(
                color=(0,0,0,1),
                width=column_2_width,
                height=20
                ),
            applyButton=dict(
                width=120
                ),
            )
        self.w = ezui.EZPanel(
            title="Rotator",
            content=content,
            descriptionData=descriptionData,
            margins=12,
            controller=self
        )
        try:
            self.w.setItemValues(getExtensionDefault(EXTENSION_KEY, self.w.getItemValues()))
        except KeyError:
            self.save_defaults()
        
        self.containers_setup = False
        self.g = CurrentGlyph()
        self.tool = getActiveEventTool()
        self.steps_text   = self.w.getItem("stepsField")
        self.steps        = self.steps_text.get()
        if self.steps:
            self.set_angle(self.steps)
        self.x_value_text = self.w.getItem("xField")
        self.x_value      = self.x_value_text.get()
        self.y_value_text = self.w.getItem("yField")
        self.y_value      = self.y_value_text.get()
        self.rounding     = self.w.getItem('roundPointsCheckbox').get()
        self.w.getNSWindow().setTitlebarHeight_(22)
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)
        self.w.setDefaultButton(self.w.getItem("applyButton"))
        self.set_point_dragging(False)
        self.recently_applied = False
        

    def started(self):
        self.glyph_editor = CurrentGlyphWindow()
        if self.glyph_editor:
            # Position the window to the top-left of your current glyph editor.
            gwx, gwy, gww, gwh = self.glyph_editor.window().getPosSize()
            wx,   wy,  ww,  wh = self.w.getPosSize()
            self.w.setPosSize((gwx + 6, gwy + 28, ww, wh))
            self.set_up_containers()
            self.draw_rotation_preview()
        self.w.open()


    def destroy(self):
        if self.containers_setup == True:
            self.bg_container.clearSublayers()
            self.pv_container.clearSublayers()
            self.containers_setup = False
        self.save_defaults()


    def save_defaults(self):
        setExtensionDefault(EXTENSION_KEY, self.w.getItemValues())
        
        
    def clear_selection(self):
        self.g.selectedContours = ()
        self.g.changed()   
        
        
    def update_x_y(self):
        self.x_value_text.set(self.x_value)
        self.y_value_text.set(self.y_value)
        self.draw_rotation_preview()
        UpdateCurrentGlyphView()
        
        
    def set_angle(self, steps):
        if steps == 0:
            self.angle = 0
        else:
            self.angle = 360 / steps
            
        # Change the angle readout in the UI
        ns_stack = self.steps_text.getNSStackView()
        ns_views = ns_stack.views()
        ns_text_field = ns_views[-1]
        ez_label = ns_text_field.vanillaWrapper()
        ez_label.set(nice_angle_string(self.angle))


     # === CALLBACKS === #
    

    def xFieldCallback(self, sender):
        x_value = sender.get()
        try:
            self.x_value = round_integer(x_value)
        except ValueError:
            x_value = self.x_value
            self.x_value_text.set(x_value)
        self.draw_rotation_preview()
        UpdateCurrentGlyphView()


    def yFieldCallback(self, sender):
        y_value = sender.get()
        try:
            self.y_value = round_integer(y_value)
        except ValueError:
            y_value = self.y_value
            self.y_value_text.set(y_value)
        self.draw_rotation_preview()
        UpdateCurrentGlyphView()
        
        
    def alignBottomButtonCallback(self, sender):
        if self.g:
            self.x_value = round_integer((self.g.bounds[2] + self.g.bounds[0]) / 2)
            self.y_value = self.g.bounds[1]
            self.update_x_y()
            
            
    def alignTopButtonCallback(self, sender):
        if self.g:
            self.x_value = round_integer((self.g.bounds[2] + self.g.bounds[0]) / 2)
            self.y_value = self.g.bounds[3]
            self.update_x_y()
            
            
    def alignLeftButtonCallback(self, sender):
        if self.g:
            self.x_value = self.g.bounds[0]
            self.y_value = round_integer((self.g.bounds[3] + self.g.bounds[1]) / 2)
            self.update_x_y()
            
            
    def alignRightButtonCallback(self, sender):
        if self.g:
            self.x_value = self.g.bounds[2]
            self.y_value = round_integer((self.g.bounds[3] + self.g.bounds[1]) / 2)
            self.update_x_y()
        
        
    def roundPointsCheckboxCallback(self, sender):
        self.rounding = sender.get()
        self.save_defaults()


    def stepsFieldCallback(self, sender):
        try:
            step_value = float(sender.get())
            step_value = int(round(step_value))
        except ValueError:
            step_value = self.w.steps_text.get()

        self.steps = step_value
        self.set_angle(self.steps)
        self.draw_rotation_preview()
        
        UpdateCurrentGlyphView()


    def strokeColorWellCallback(self, sender):
        self.draw_rotation_preview()


    def applyButtonCallback(self, sender):
        with self.g.undo('Rotator: Apply Rotation'):
            self.g.appendGlyph(self.get_rotated_glyph())
        self.save_defaults()
        self.g.changed()
        # Remove everything but the crosshairs
        if self.stroked_preview:
            self.stroked_preview.setPath(None)
            self.recently_applied = True


    # === SUBSCRIBERS === #


    def glyphEditorDidSetGlyph(self, info):
        if self.containers_setup == True:
            self.bg_container.clearSublayers()
            self.pv_container.clearSublayers()
            self.containers_setup = False
        self.g = info["glyph"]
        self.glyph_editor = info["glyphEditor"]
        self.set_up_containers()
        self.draw_rotation_preview()
        

    glyphEditorGlyphDidChangeDelay = 0
    def currentGlyphDidChangeContours(self, info):
        self.g = info["glyph"]
        self.draw_rotation_preview()
        

    def glyphEditorDidMouseDown(self, info):
        self.down_point = (info['lowLevelEvents'][0]['point'].x, info['lowLevelEvents'][0]['point'].y)
        self.g = info["glyph"]
        if is_near(self.down_point, (self.x_value, self.y_value)):
            self.set_point_dragging(True)
            self.clear_selection()
            self.mouse_update_origin(info)
        else:
            self.set_point_dragging(False)
            if self.recently_applied == False:
                self.mouse_update_origin(info)
        

    def set_point_dragging(self, value):
        if value == False:
            self.point_dragging = False
            # self.tool.shouldShowMarqueRect = enable
            # self.tool.canSelectWithMarque  = enable
            # print("self.tool.shouldShowMarqueRect = enable, self.tool.canSelectWithMarque  = enable")        
        else:
            self.point_dragging = True
            self.recently_applied = False  # You may have hit Apply earlier, but now things can start moving.
            # self.tool.shouldShowMarqueRect = disable
            # self.tool.canSelectWithMarque  = disable
            # print("self.tool.shouldShowMarqueRect = disable, self.tool.canSelectWithMarque  = disable") 
    

    glyphEditorDidMouseDragDelay = 0
    def glyphEditorDidMouseDrag(self, info):
        self.g = info["glyph"]
        if self.recently_applied == False:
            self.mouse_update_origin(info)
        
        
    def glyphEditorDidUndo(self, info):
        self.recently_applied = False
        self.draw_rotation_preview()
        

    def glyphEditorDidMouseUp(self, info):
        self.g = info["glyph"]
        
        # Deselect stuff if you just came back from dragging
        if self.point_dragging:
            self.clear_selection()  
            self.mouse_update_origin(info)      
        self.set_point_dragging(False)    
        if self.recently_applied == False:
            self.mouse_update_origin(info)                    
        
        
    def glyphEditorWillOpen(self, info):
        self.glyph_editor = info["glyphEditor"]
        self.set_up_containers()
        
        
    def glyphEditorDidOpen(self, info):
        self.draw_rotation_preview()


    # === MERZ === #


    def set_up_containers(self):
        self.bg_container = self.glyph_editor.extensionContainer(
            identifier="rotator.foreground", 
            location="foreground", 
            clear=True
            )
        self.pv_container = self.glyph_editor.extensionContainer(
            identifier="rotator.preview", 
            location="preview", 
            clear=True
            )
        self.containers_setup = True


    def mouse_update_origin(self, info):
        point = info['lowLevelEvents'][0]['point']
        if self.point_dragging:
            self.x_value, self.y_value = round_integer(point.x), round_integer(point.y)
            self.x_value_text.set(self.x_value)
            self.y_value_text.set(self.y_value)
        self.draw_rotation_preview()


    def draw_rotation_preview(self):
        self.bg_container.clearSublayers()
        self.pv_container.clearSublayers()
        
        # Draw outlined glyph
        self.stroked_preview = self.bg_container.appendPathSublayer(
                strokeColor=self.w.getItem('strokeColorWell').get(),
                fillColor=None,
                strokeWidth=1
            )
        outline = self.get_rotated_glyph()
        glyph_path = outline.getRepresentation("merz.CGPath")
        self.stroked_preview.setPath(glyph_path)
        
        # Draw solid preview
        default_preview_color = getDefault('glyphViewPreviewFillColor')
        self.filled_preview = self.pv_container.appendPathSublayer(
                strokeColor=None,
                fillColor=default_preview_color,
                strokeWidth=0
            )
        self.filled_preview.setPath(glyph_path)

        # Draw crosshair
        center_x = self.x_value
        center_y = self.y_value
        self.crosshair = self.bg_container.appendSymbolSublayer(
            position        = (center_x, center_y),
            imageSettings   = dict(
                                name        = "rotator.circleCrosshair",
                                strokeColor = (1,0,0,0.8)
                                )
            )
        self.previewCrosshair = self.pv_container.appendSymbolSublayer(
            position        = (center_x, center_y),
            imageSettings   = dict(
                                name        = "rotator.circleCrosshair",
                                strokeColor = (1,0,0,0.8)
                                )
            )


    def get_rotated_glyph(self):
        x = round_integer(self.x_value_text.get())
        y = round_integer(self.y_value_text.get())

        if x == None or y == None:
            x = self.g.width / 2
            y = (self.g.bounds[3] - self.g.bounds[1]) / 2

        steps = self.steps
        angle = self.angle

        center = (x, y)
        rotation_result_glyph = RGlyph()
        rotation_step_glyph = RGlyph()
        pen = rotation_step_glyph.getPointPen()

        contour_list = []
        for idx, contour in enumerate(self.g):
            if contour.selected:
                contour_list.append(idx)

        # if nothing is selected, the whole glyph will be rotated.
        if len(contour_list) == 0:
            for idx, contour in enumerate(self.g):
                contour_list.append(idx)

        for contour in contour_list:
            self.g[contour].drawPoints(pen)

        # Don't draw the original shape again
        step_count = steps - 1

        for i in range(step_count):
            rotation_step_glyph.rotateBy(angle, center)
            rotation_result_glyph.appendGlyph(rotation_step_glyph)

        if self.rounding:
            rotation_result_glyph.round()

        return rotation_result_glyph
            
registerRoboFontSubscriber(Rotator)