from AppKit import NSColor
from lib.tools.misc import NSColorToRgba
from fontTools.pens.cocoaPen import CocoaPen
from lib.UI.integerEditText import NumberEditText
from mojo.UI import getDefault, UpdateCurrentGlyphView

from mojo.extensions import (
    getExtensionDefault, setExtensionDefault,
    getExtensionDefaultColor, setExtensionDefaultColor)
from vanilla import (
    Button, CheckBox, ColorWell, EditText,
    FloatingWindow, HorizontalLine, TextBox)

import merz
from merz.tools.drawingTools import NSImageDrawingTools
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber

rotatorDefaults = 'de.frgr.Rotator'

def rotatorSymbolFactory(
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
    # return the image
    return bot.getImage()
    
merz.SymbolImageVendor.registerImageFactory("rotator.crosshair", rotatorSymbolFactory)


class Rotator(Subscriber):

    _title = 'Rotator'
    _width = 178
    _frame = 10
    _height = 0 # this will happen dynamically based on textboxY
    _row = 30
    _padding = 14
    _gutter = 6
    _lineHeight = 24
    _color = (0.0, 0.5, 1.0, .8)

    _columns = 3
    _col_width = (_width - ((_columns - 1) * _gutter)) / _columns
    _col_0 = _frame
    _col_1 = _frame + _col_width + _gutter
    _col_2 = _frame + 2 * _col_width + 2 * _gutter
    _col_3 = _frame + 3 * _col_width + 3 * _gutter

    xValue = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'x'), 0)
    yValue = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'y'), 0)
    steps = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'steps'), 12)
    lock = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'lock'), False)
    rounding = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'round'), False)
    angle = 360.0 / steps
    

    def build(self):

        self.w = FloatingWindow(
            (self._width + 2 * self._frame, self._height),
            self._title)
        self.w.getNSWindow().setTitlebarHeight_(22)
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)

        # ----------
        # text boxes
        # ----------

        textBoxY = self._padding

        self.w.steps_label = TextBox(
            (self._col_0, textBoxY, self._col_width, self._lineHeight),
            'Steps', alignment='right')

        self.w.steps_text = NumberEditText(
            (self._col_1, textBoxY - 2, self._col_width, self._lineHeight),
            self.steps,
            callback=self.angleCallback,
            allowFloat=False,
            allowNegative=False,
            allowEmpty=False,
            minimum=1,
            decimals=0,
            continuous=True)
        self.w.steps_text.getNSTextField().setFocusRingType_(1)
                
        self.w.color = ColorWell(
            (self._col_2, textBoxY - 1, -self._frame, self._lineHeight - 1),
            color=getExtensionDefaultColor(
                '%s.%s' % (rotatorDefaults, 'color'), self._color),
            callback=self.colorCallback)
        
        self._color = NSColorToRgba(self.w.color.get())

        textBoxY += (self._row)

        self.w.xValue_label = TextBox(
            (self._col_0, textBoxY, self._col_width, self._lineHeight),
            'x', alignment='right')

        self.w.xValue_text = NumberEditText(
            (self._col_1, textBoxY - 2, self._col_width, self._lineHeight),
            self.xValue,
            callback=self.xCallback,
            allowFloat=True,
            decimals=0)
        self.w.xValue_text.getNSTextField().setFocusRingType_(1)
        
        textBoxY += (self._row)

        self.w.yValue_label = TextBox(
            (self._col_0, textBoxY, self._col_width, self._lineHeight),
            'y', alignment='right')

        self.w.yValue_text = NumberEditText(
            (self._col_1, textBoxY - 2, self._col_width, self._lineHeight),
            self.yValue,
            callback=self.yCallback,
            allowFloat=True,
            decimals=0)
        self.w.yValue_text.getNSTextField().setFocusRingType_(1)
            
        textBoxY += (self._row)

        self.w.angle_label = TextBox(
            (self._col_0, textBoxY, self._col_width, self._lineHeight),
            'Angle', alignment='right')
        self.w.angleResult = TextBox(
            (self._col_1, textBoxY, self._col_width, self._lineHeight),
            u'%s°' % self.niceAngleString(self.angle))

        textBoxY += (self._row)

        self.w.line = HorizontalLine(
            (self._gutter, textBoxY, -self._gutter, 0.5))

        textBoxY += (self._row*0.2)

        self.w.lock_checkbox = CheckBox(
            (self._col_1 - 25, textBoxY, -self._gutter, self._lineHeight),
            'Lock Center',
            value=self.lock,
            callback=self.lockCallback)
            
        textBoxY += (self._row*0.8)

        self.w.rounding_checkbox = CheckBox(
            (self._col_1 - 25, textBoxY, -self._gutter, self._lineHeight),
            'Round Result',
            value=self.rounding,
            callback=self.roundingCallback)
        textBoxY += (self._row)

        # -------
        # buttons
        # -------
        
        textBoxY += (self._row * 1.2)
        
        self.w.buttonRotate = Button(
            (self._col_0, -self._col_0 - self._lineHeight, -self._col_0, self._lineHeight),
            'Rotate',
            callback=self.rotateCallback)

        self.w.setDefaultButton(self.w.buttonRotate)
        self.w.open()
        w_x, w_y, w_w, w_h = self.w.getPosSize()
        self.w.resize(w_w, textBoxY)

        self.glyph_editor = self.getGlyphEditor()
        self.bg_container = self.glyph_editor.extensionContainer(
            identifier="rotator.background", 
            location="background", 
            clear=True
            )
        self.drawRotationPreview()
        

    def getRotatedGlyph(self):
        glyph = CurrentGlyph()
        x = int(self.w.xValue_text.get())
        y = int(self.w.yValue_text.get())

        steps = self.steps
        angle = self.angle

        center = (x, y)
        rotation_result_glyph = RGlyph()
        rotation_step_glyph = RGlyph()
        pen = rotation_step_glyph.getPointPen()

        contourList = []
        for idx, contour in enumerate(glyph):
            if contour.selected:
                contourList.append(idx)

        # if nothing is selected, the whole glyph will be rotated.
        if len(contourList) == 0:
            for idx, contour in enumerate(glyph):
                contourList.append(idx)

        for contour in contourList:
            glyph[contour].drawPoints(pen)

        # don't draw the original shape again
        stepCount = steps - 1

        if steps < 2:  # solution/hack for 1-step rotation
            stepCount = 1
            angle = 90

        for i in range(stepCount):
            rotation_step_glyph.rotateBy(angle, center)
            rotation_result_glyph.appendGlyph(rotation_step_glyph)

        if self.rounding:
            rotation_result_glyph.round()

        return rotation_result_glyph

    def updateOrigin(self, info):
        point = info['lowLevelEvents'][0]['point']
        if not self.lock:
            self.xValue, self.yValue = int(round(point.x)), int(round(point.y))
            self.w.xValue_text.set(self.xValue)
            self.w.yValue_text.set(self.yValue)
            self.drawRotationPreview()

    def drawRotationPreview(self):
        self.bg_container.clearSublayers()
        # draw preview glyph
        self.stroked_preview = self.bg_container.appendPathSublayer(
                strokeColor=self._color,
                fillColor=None,
                strokeWidth=1
            )
        outline = self.getRotatedGlyph()
        glyph_path = outline.getRepresentation("merz.CGPath")
        self.stroked_preview.setPath(glyph_path)

        # # draw crosshair
        center_x = self.xValue
        center_y = self.yValue
        self.crosshair = self.bg_container.appendSymbolSublayer(
            position        = (center_x, center_y),
            imageSettings   = dict(
                                name        = "rotator.crosshair",
                                strokeColor = (1,0,0,0.8)
                                )
            )

    def drawSolidPreview(self, info):
        # THIS ISN'T UPDATED TO SUBSCRIBER YET
        outline = self.getRotatedGlyph()
        pen = CocoaPen(None)
        outline.draw(pen)
        defaultPreviewColor = getDefault('glyphViewPreviewFillColor')
        fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            *defaultPreviewColor)
        fillColor.set()
        pen.path.fill()
    
    
     # === CALLBACKS === #
    
    def xCallback(self, sender):
        xValue = sender.get()
        try:
            self.xValue = int(xValue)
        except ValueError:
            xValue = self.xValue
            self.w.xValue_text.set(xValue)

        UpdateCurrentGlyphView()

    def yCallback(self, sender):
        yValue = sender.get()
        try:
            self.yValue = int(yValue)
        except ValueError:
            yValue = self.yValue
            self.w.yValue_text.set(yValue)

        UpdateCurrentGlyphView()

    def lockCallback(self, sender):
        self.lock = not self.lock
        self.saveDefaults()

    def roundingCallback(self, sender):
        self.rounding = not self.rounding
        self.saveDefaults()

    def angleCallback(self, sender):
        try:
            stepValue = float(sender.get())
            stepValue = int(round(stepValue))
        except ValueError:
            stepValue = self.steps
            self.w.steps_text.set(self.steps)

        self.steps = stepValue

        if abs(stepValue) < 2:
            self.angle = 90.0

        elif stepValue == 0:
            self.angle = 0

        else:
            self.angle = 360 / stepValue

        self.w.angleResult.set(u'%s°' % self.niceAngleString(self.angle))
        UpdateCurrentGlyphView()

    def niceAngleString(self, angle):
        angleResultString = u'%.2f' % angle
        if angleResultString.endswith('.00'):
            angleResultString = angleResultString[0:-3]
        return angleResultString

    def colorCallback(self, sender):
        setExtensionDefaultColor(
            '%s.%s' % (rotatorDefaults, 'color'), sender.get())
        self._color = NSColorToRgba(sender.get())
        self.drawRotationPreview()
    
    def saveDefaults(self):
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'x'), self.xValue)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'y'), self.yValue)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'steps'), self.steps)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'lock'), self.lock)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'round'), self.rounding)

    def rotateCallback(self, sender):
        with self.g.undo('Rotator'):
            rotatedGlyph = self.getRotatedGlyph()
            self.g.appendGlyph(rotatedGlyph)
        self.saveDefaults()
        self.g.changed()
        
    def windowCloseCallback(self, sender):
        self.bg_container.clearSublayers()
        unregisterGlyphEditorSubscriber(Rotator)
        # UpdateCurrentGlyphView()
        self.saveDefaults()
        
        
    # === SUBSCRIBERS === #

    def glyphEditorDidSetGlyph(self, info):
        self.g = info["glyph"]
        self.drawRotationPreview() 
        
    glyphEditorGlyphDidChangeDelay = 0
    def glyphEditorGlyphDidChange(self, info):
        self.g = info["glyph"]
        self.drawRotationPreview()
    
    glyphEditorDidMouseDragDelay = 0
    def glyphEditorDidMouseDrag(self, info):
        self.g = info["glyph"]
        self.updateOrigin(info)
        
    def glyphEditorDidMouseUp(self, info):
        self.g = info["glyph"]
        self.updateOrigin(info)

    
g = CurrentGlyph()
if g:
    registerGlyphEditorSubscriber(Rotator)
else:
    print('Please open a glyph window.')
