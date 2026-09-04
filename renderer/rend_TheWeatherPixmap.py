import os
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, loadPNG

class rend_TheWeatherPixmap(Renderer):
    def __init__(self):
        Renderer.__init__(self)
        self.path = "/usr/lib/enigma2/python/Plugins/Extensions/TheWeather/Images/iconhd/"

    GUI_WIDGET = ePixmap

    def postWidgetCreate(self, instance):
        self.changed((self.CHANGED_DEFAULT,))

    def changed(self, who):
        if self.instance is not None:
            if self.source:
                icon_code = self.source.text
                if icon_code and icon_code != "N/A":
                    # Endung .png nur anfügen, falls nicht schon vorhanden
                    if not icon_code.endswith(".png"):
                        filename = os.path.join(self.path, "%s.png" % icon_code)
                    else:
                        filename = os.path.join(self.path, icon_code)

                    if os.path.exists(filename):
                        try:
                            ptr = loadPNG(filename)
                            if ptr is not None:
                                self.instance.setPixmap(ptr)
                                self.instance.show()
                                return
                        except Exception as e:
                            print("[rend_TheWeatherPixmap] Error loading PNG:", e)

            # Falls kein Icon gefunden wird oder ein Fehler auftritt -> Ausblenden
            self.instance.hide()
