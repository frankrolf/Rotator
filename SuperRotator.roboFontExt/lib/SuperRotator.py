# coding: utf-8

import os
import plistlib

from vanilla import *
from AppKit import *

from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
from mojo.events import BaseEventTool
from mojo.glyphPreview import GlyphPreview
from mojo.UI import UpdateCurrentGlyphView
from fontTools.pens.cocoaPen import CocoaPen
from lib.fontObjects import internalFontClasses
from mojo.extensions import getExtensionDefault, setExtensionDefault, getExtensionDefaultColor, setExtensionDefaultColor

rotatorPaletteDefaultKey = "de.frgr.SuperRotator"

def getPrefs():
    prefPath = os.path.expanduser('~/Library/Preferences/')
    prefFile = os.sep.join((prefPath, 'de.frgr.SuperRotator.plist'))


    'standard plist values'
    prefDict = {
        'steps': 6,
        'x': 0,
        'y': 0,
        'capture': False,
        'round': True,
    }

    # write standard values in prefs file if it does not exist, or the keys are different.
    if not os.path.exists(prefFile):
        plistlib.writePlist(prefDict, prefFile)
    if sorted(plistlib.readPlist(prefFile).keys()) != sorted(prefDict.keys()):
        plistlib.writePlist(prefDict, prefFile)

    prefDict.update(plistlib.readPlist(prefFile))
    return prefDict


# def writePrefs(prefDict):
#     storedPrefs = 


# prefDict['pointsize'] = pointsize
# prefDict['targetLineWidth'] = targetLineWidth
# prefDict['splitGlyphName'] = splitGlyphName
# plistlib.writePlist(prefDict, prefFile)


class SuperRotator(BaseWindowController):

    _title = 'SuperRotator'
    _width = 140
    _frame = 8
    _height = 260
    _row = 24
    _padding = 16
    _gutter = 8
    _lineHeight = 20

    _columns = 2
    _columnWidth = (_width-((_columns-1)*_gutter))/_columns
    _column_0 = _frame
    _column_1 = _frame + _columnWidth + _gutter
    _column_2 = _frame + 2*_columnWidth + 2*_gutter
    _column_3 = _frame + 3*_columnWidth + 3*_gutter

    # print _column_1,_column_2,_column_3
    # print _column_0+_columnWidth,_column_1+_columnWidth,_column_2+_columnWidth,_column_3+_columnWidth
    # _column_2 = _width * 1/2 
    # _column_3 = _width * 3/4 

    preferences = getPrefs()

    _xValue = preferences['x']
    _yValue = preferences['y']
    _steps = preferences['steps']
    _capture = preferences['capture']
    _round = preferences['round']
    _angle = 360.0/_steps


    def __init__(self):
        self.glyph = CurrentGlyph()

        self.w = FloatingWindow(
                (self._width+2*self._frame, self._height),
                self._title, textured=True, closable=True)

        # _xValue = int(self.glyph.width/2)
        self.coords = (self._xValue,self._yValue)
        # self.activateClickCapture()

        # text boxes
        # ----------

        textBoxY = self._padding

        self.w.steps_label = TextBox(
                (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
                'steps', alignment='right')
        
        self.w.steps_text = EditText(
                (self._column_1, textBoxY-2, self._columnWidth, self._lineHeight), 
                self._steps, callback=self.angleCallback, continuous=True)

        textBoxY += (self._row)

        self.w.xValue_label = TextBox(
                (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
                'x', alignment='right')
        self.w.xValue_text = EditText(
                (self._column_1, textBoxY-2, self._columnWidth, self._lineHeight),
                self._xValue, callback=self.updateCallback)

        textBoxY += (self._row)

        self.w.yValue_label = TextBox(
                (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
                'y', alignment='right')
        self.w.yValue_text = EditText(
                (self._column_1, textBoxY-2, self._columnWidth, self._lineHeight),
                self._yValue, callback=self.updateCallback)

        textBoxY += (self._row)

        self.w.angle_label = TextBox(
                (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
                'angle', alignment='right')
        self.w.angleResult = TextBox(
                (self._column_1, textBoxY, self._columnWidth, self._lineHeight),
                u'%s°' % int(self._angle))

        textBoxY += (self._row)

        # self.w.capture_label = TextBox(
        #         (self._column_0, textBoxY, self._columnWidth, self._lineHeight),
        #         'Capture clicks', alignment='right')
        self.w.capture_checkbox = CheckBox(
                (self._column_0, textBoxY, self._columnWidth*2, self._lineHeight),
                'capture clicks', value=self._capture)

        textBoxY += (self._row)

        self.w.round_checkbox = CheckBox(
                (self._column_0, textBoxY, self._columnWidth*2, self._lineHeight),
                'round coords', value=self._round)


        # self.w.decorationLeft = TextBox(
        #         (self._column_0, textBoxY, self._columnWidth, 4*self._lineHeight),
        #         # u'✼ ✢ ✱ ✤\n✤ ✼ ✢ ✱\n✱ ✤ ✼ ✢\n✢ ✱ ✤ ✼', alignment='right')
        #         u'✼ ✢ ✱\n✤ ✼ ✢\n✱ ✤ ✼\n✢ ✱ ✤', alignment='right')

        # self.w.decorationRight = TextBox(
        #         (self._column_1, textBoxY, self._columnWidth, 4*self._lineHeight),
        #         # u'✼ ✢ ✱ ✤\n✤ ✼ ✢ ✱\n✱ ✤ ✼ ✢\n✢ ✱ ✤ ✼', alignment='left')
        #         u'✢ ✱ ✤\n✼ ✢ ✱\n✤ ✼ ✢\n✱ ✤ ✼', alignment='left')


        # buttons
        # -------

        self.w.buttonClose = Button(
                (self._column_0, -60, 2*self._columnWidth+self._gutter, 25),
                'Close',
                callback=self.closeCallback)

        self.w.buttonRotate = Button(
                (self._column_0, -30, 2*self._columnWidth+self._gutter, 25),
                'Rotate',
                callback=self.rotateCallback)



        self.setUpBaseWindowBehavior()

        addObserver(self, 'mouseUp', 'mouseUp')
        # addObserver(self, 'modifiersChanged', 'modifiersChanged')
        addObserver(self, 'drawRotationPreview', 'drawBackground')
        self.w.setDefaultButton(self.w.buttonRotate)
        # self.w.bind('became key', self.activateClickCapture)
        self.w.open()



    def drawRotationPreview(self, info):

        outline = self.getRotatedGlyph()
        pen = CocoaPen(None)
        outline.draw(pen)

        nscolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.8, .8)
        color = getExtensionDefaultColor("%s.%s" %(rotatorPaletteDefaultKey, "color"), nscolor)
        # print getExtensionDefaultColor()
        # pen.path.fill()
        pen.path.stroke()



    # def drawDisplayGlyph(self):
    #     displayGlyph = RGlyph()
    #     displayGlyph.width = 0 # self.glyph.width
    #     displayPen = displayGlyph.getPen()
    #     coords = (0,0)


    #     displayGlyph.scale((3, 3), coords)
    #     displayGlyph.move((0, 250))


    #     return displayGlyph


    def mouseUp(self, info):
        pass
        # if self.captureClickCoords:

        #     self.coords = int(round(info['point'].x)), int(round(info['point'].y))
        #     self.w.xValue_text.set(self.coords[0])
        #     self.w.yValue_text.set(self.coords[1])
        # else:
        #     pass

    def updateCallback(self, sender):
        UpdateCurrentGlyphView()


    def activateClickCapture(self, sender=None):
        self.captureClickCoords = True


    def modifiersChanged(self, info):
        'Do not capture mouse coordinates when modifier key is down'
        self.captureClickCoords = not self.captureClickCoords


    def angleCallback(self, sender):
        stepValue = float(sender.get())
        stepValue = int(round(stepValue))
        self._steps = stepValue

        if abs(stepValue) < 2:
            self._angle = 90.0

        elif stepValue == 0:
            self._angle = 0
        
        else:    
            self._angle = 360/stepValue

        result = int(self._angle) if str(self._angle).endswith('.0') else round(self._angle,2)
        self._angle = result
        self.w.angleResult.set(u'%s°' % result)
        UpdateCurrentGlyphView()


    def closeCallback(self, sender):
        removeObserver(self, 'mouseUp')
        # removeObserver(self, 'modifiersChanged')
        removeObserver(self, 'drawBackground')
        UpdateCurrentGlyphView()
        self.w.close()
    

    def windowCloseCallback(self, sender):
        removeObserver(self, 'mouseUp')
        # removeObserver(self, 'modifiersChanged')
        removeObserver(self, 'drawBackground')
        UpdateCurrentGlyphView()
        # self.w.close()
        # super(SuperRotator, self).windowCloseCallback(sender)


    def rotateCallback(self, sender):
        self.glyph.prepareUndo('Rotate')
        rotatedGlyph = self.getRotatedGlyph()

        self.glyph.appendGlyph(rotatedGlyph)        
        self.glyph.performUndo()
        self.glyph.update()


    def getRotatedGlyph(self):

        x = int(self.w.xValue_text.get())
        y = int(self.w.yValue_text.get())

        steps = self._steps
        angle = self._angle
        center = (x, y)
        rGlyph = RGlyph()
        pen = rGlyph.getPointPen()
        contourList = []
        for idx, contour in enumerate(self.glyph):
            if contour.selected:
                contourList.append(idx)
        
        if len(contourList) == 0: # if nothing is selected, the whole glyph will be rotated.
            for idx, contour in enumerate(self.glyph):
                contourList.append(idx)
        
        for contour in contourList:
            self.glyph[contour].drawPoints(pen)
        

        stepCount = steps - 1

        if steps < 2: 
            stepCount = 1
            angle = 90

        # tempGlyph = internalFontClasses.createGlyphObject()
        tempGlyph = RGlyph()
        tempGlyph.appendGlyph(rGlyph)

        for i in range(1, stepCount+1):
            tempGlyph.rotate(angle, center)
            rGlyph.appendGlyph(tempGlyph)
            # pen = tempGlyph.getPointPen()
            # rGlyph.drawPoints(pen)
            
        return rGlyph

        # prefDict['pointsize'] = pointsize
        # prefDict['targetLineWidth'] = targetLineWidth
        # prefDict['splitGlyphName'] = splitGlyphName
        # plistlib.writePlist(prefDict, prefFile)



OpenWindow(SuperRotator)
