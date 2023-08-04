# Rotator
<!-- <img src="rotator.png" width="640" height="440" alt="Rotators gonna Rotate" /> -->
<img src="./_images/demo.png">

The rotation center can be set by entering coordinate values, or by dragging the crosshair center across the canvas. 
A preview of the rotation is shown in the glyph window; and will dynamically update when new values are given, or other outlines are selected. 


## Versions
    1.1   2023-08-03  EZUI, better Merz + Subscriber, click-drag crosshair
    1.0   2022-03-17  Support for RF4 - Merz + Subscriber
    0.6.0 2019-12-16  Allow dragging, add crosshair cursor
    0.5.3 2019-10-18  Do not limit to a single glyph 
                      (which means the window can stay open while toggling through fonts)
    0.5.2 2019-10-17  Limit imports
    0.5.1 2018-02-07  Python 3 support and some common sense modifications.
                      (Why wouldn’t the window be closeable in a normal way?
                      That was silly.)
    0.5   2015-03-01  Make text boxes better with digesting (ignoring)
                      malicious input.
    0.4   2014-07-30  Update UI, get rid of plist files, add preview glyph,
                      add optional rounding for resulting glyph.
    0.3   2013-11-08  Add click capture for setting rotation center.
    0.2   2013-03     Re-write for Robofont.
    0.1   2013-02-28  Update with plist for storing preferences.
    0.0   2012        FL version.


## Background

I originally wrote this when drawing [Zapf Dingbats](http://en.wikipedia.org/wiki/Zapf_Dingbats) for [FF Quixo](https://www.fontfont.com/fonts/quixo):

<p style='font-family:"Zapf Dingbats";'>
    ✁✂✃✄✅✆✇✈✉✊✋✌✍✎✏✐✑✒<br>
    ✓✔✕✖✗✘✙✚✛✜✝✞✟✠✡✢✣✤✥✦✧✨✩<br>
    ✪✫✬✭✮✯✰✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿<br>
    ❀❁❂❃❄❅❆❇❈❉❊❋❌❍❎❏❐❑❒❓❔<br>
    ❕❖❗❘❙❚❛❜❝❞❟❠❡❢❣❤❥❦❧❨❩❪❫❬❭❮❯❰❱❲❳❴❵<br>    
    ❶❷❸❹❺❻❼❽❾❿➀➁➂➃➄➅➆➇➈➉<br>
    ➊➋➌➍➎➏➐➑➒➓➔➕➖➗<br>
    ➘➙➚➛➜➝➞➟➠➡➢➣➤➥➦➧➨➩➪➫<br>
    ➬➭➮➯➰➱➲➳➴➵➶➷➸➹➺➻➼➽➾<br>
</p>
This script was very useful for the flowery- and asterisky glyphs. No procrastination involved whatsoever!


## MIT License

Copyright (c) 2015 Frank Grießhammer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
