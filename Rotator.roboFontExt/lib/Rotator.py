# coding: utf-8

'''
ЯOTATOR.

Robofont extension for joyful rotation of whole glyphs or selected outlines.
✱ ✲ ✳ ✴ ✵ ✶ ✷ ✸ ✹ ✺ ✻ ✼ ✽ ✾ ✿ ❀ ❁ ❂ ❃ ❄ ❅ ❆ ❇ ❈ ❉ ❊ ❋
Frank Grießhammer – www.frgr.de

Versions:
0.5.1 2018-02-07  Python 3 support
0.5   2015-03-01  Make text boxes better with digesting (ignoring)
                  malicious input.
0.4   2014-07-30  Update UI, get rid of plist files, add preview glyph,
                  add optional rounding for resulting glyph.
0.3   2013-11-08  Add click capture for setting rotation center.
0.2   2013-03     Re-write for Robofont.
0.1   2013-02-28  Update with plist for storing preferences.
0.0   2012        FL version.

'''


from vanilla import *
from AppKit import *

from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
# from mojo.events import BaseEventTool
# from mojo.glyphPreview import GlyphPreview
from mojo.UI import UpdateCurrentGlyphView
from fontTools.pens.cocoaPen import CocoaPen
from mojo.extensions import \
    getExtensionDefault, setExtensionDefault, \
    getExtensionDefaultColor, setExtensionDefaultColor

rotatorDefaults = 'de.frgr.Rotator'


class Rotator(BaseWindowController):

    _title = 'Rotator'
    _width = 180
    _frame = 8
    _height = 274
    _row = 24
    _padding = 16
    _gutter = 8
    _lineHeight = 20
    _color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
        0.0, 0.5, 1.0, .8)

    _columns = 3
    _columnWidth = (_width - ((_columns - 1) * _gutter)) / _columns
    _column_0 = _frame
    _column_1 = _frame + _columnWidth + _gutter
    _column_2 = _frame + 2 * _columnWidth + 2 * _gutter
    _column_3 = _frame + 3 * _columnWidth + 3 * _gutter

    xValue = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'x'), 0)
    yValue = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'y'), 0)
    steps = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'steps'), 12)
    capture = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'capture'), False)
    rounding = getExtensionDefault(
        '%s.%s' % (rotatorDefaults, 'round'), False)
    angle = 360.0 / steps

    def __init__(self, glyph):

        self.glyph = glyph
        self.w = FloatingWindow(
            (self._width + 2 * self._frame, self._height),
            self._title, textured=True, closable=False)

        # ----------
        # text boxes
        # ----------

        textBoxY = self._padding

        self.w.steps_label = TextBox(
            (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
            'Steps', alignment='right')
        self.w.steps_text = EditText(
            (self._column_1, textBoxY - 2, self._columnWidth, self._lineHeight),
            self.steps,
            callback=self.angleCallback,
            continuous=True)
        textBoxY += (self._row)

        self.w.xValue_label = TextBox(
            (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
            'x', alignment='right')
        self.w.xValue_text = EditText(
            (self._column_1, textBoxY - 2, self._columnWidth, self._lineHeight),
            self.xValue,
            callback=self.xCallback)
        textBoxY += (self._row)

        self.w.yValue_label = TextBox(
            (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
            'y', alignment='right')
        self.w.yValue_text = EditText(
            (self._column_1, textBoxY - 2, self._columnWidth, self._lineHeight),
            self.yValue,
            callback=self.yCallback)
        textBoxY += (self._row)

        self.w.angle_label = TextBox(
            (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
            'Angle', alignment='right')
        self.w.angleResult = TextBox(
            (self._column_1, textBoxY, self._columnWidth, self._lineHeight),
            u'%s°' % self.niceAngleString(self.angle))
        textBoxY += (self._row)

        textBoxY += (self._row * .25)
        self.w.line = HorizontalLine(
            (self._gutter, textBoxY, -self._gutter, 0.5))
        textBoxY += (self._row * .25)

        self.w.capture_checkbox = CheckBox(
            (self._column_1 - 25, textBoxY, -self._gutter, self._lineHeight),
            'Capture Clicks',
            value=self.capture,
            callback=self.captureCallback)
        textBoxY += (self._row)

        self.w.rounding_checkbox = CheckBox(
            (self._column_1 - 25, textBoxY, -self._gutter, self._lineHeight),
            'Round Result',
            value=self.rounding,
            callback=self.roundingCallback)
        textBoxY += (self._row)

        # -------
        # buttons
        # -------

        self.w.color = ColorWell(
            (self._column_0, textBoxY, -self._gutter, 2 * self._lineHeight),
            color=getExtensionDefaultColor(
                '%s.%s' % (rotatorDefaults, 'color'), self._color),
            callback=self.colorCallback)

        textBoxY += (self._row)

        self.w.buttonClose = Button(
            (self._column_0, -55, -self._gutter, self._lineHeight),
            'Close',
            callback=self.closeCallback)

        self.w.buttonRotate = Button(
            (self._column_0, -30, -self._gutter, self._lineHeight),
            'Rotate',
            callback=self.rotateCallback)

        self.setUpBaseWindowBehavior()
        addObserver(self, 'mouseUp', 'mouseUp')
        addObserver(self, 'drawRotationPreview', 'drawBackground')
        self.w.setDefaultButton(self.w.buttonRotate)
        self.w.open()

    def drawRotationPreview(self, info):
        outline = self.getRotatedGlyph()
        pen = CocoaPen(None)
        self.w.color.get().set()
        outline.draw(pen)
        # pen.path.fill()
        pen.path.setLineWidth_(0.5)
        pen.path.stroke()

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

    def captureCallback(self, sender):
        self.capture = not self.capture
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
        UpdateCurrentGlyphView()

    def closeCallback(self, sender):
        removeObserver(self, 'mouseUp')
        removeObserver(self, 'drawBackground')
        UpdateCurrentGlyphView()
        self.saveDefaults()
        self.w.close()

    def windowCloseCallback(self, sender):
        removeObserver(self, 'mouseUp')
        removeObserver(self, 'drawBackground')
        UpdateCurrentGlyphView()
        self.saveDefaults()

    def mouseUp(self, info):
        if self.capture:
            self.xValue, self.yValue = int(
                round(info['point'].x)), int(round(info['point'].y))
            self.w.xValue_text.set(self.xValue)
            self.w.yValue_text.set(self.yValue)

    def saveDefaults(self):
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'x'), self.xValue)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'y'), self.yValue)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'steps'), self.steps)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'capture'), self.capture)
        setExtensionDefault(
            '%s.%s' % (rotatorDefaults, 'round'), self.rounding)

    def rotateCallback(self, sender):
        self.glyph.prepareUndo('Rotator')
        rotatedGlyph = self.getRotatedGlyph()

        self.glyph.appendGlyph(rotatedGlyph)
        self.glyph.performUndo()
        self.saveDefaults()
        self.glyph.update()

    def getRotatedGlyph(self):
        x = int(self.w.xValue_text.get())
        y = int(self.w.yValue_text.get())

        steps = self.steps
        angle = self.angle

        center = (x, y)
        rotationResultGlyph = RGlyph()
        rotationStepGlyph = RGlyph()
        pen = rotationStepGlyph.getPointPen()

        contourList = []
        for idx, contour in enumerate(self.glyph):
            if contour.selected:
                contourList.append(idx)

        # if nothing is selected, the whole glyph will be rotated.
        if len(contourList) == 0:
            for idx, contour in enumerate(self.glyph):
                contourList.append(idx)

        for contour in contourList:
            self.glyph[contour].drawPoints(pen)

        # don't draw the original shape again
        stepCount = steps - 1

        if steps < 2:  # solution/hack for 1-step rotation
            stepCount = 1
            angle = 90

        for i in range(stepCount):
            rotationStepGlyph.rotate(angle, center)
            rotationResultGlyph.appendGlyph(rotationStepGlyph)

        if self.rounding:
            rotationResultGlyph.round()

        return rotationResultGlyph


g = CurrentGlyph()
if g:
    OpenWindow(Rotator, g)
else:
    print('Please open a glyph window.')
