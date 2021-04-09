from .frame_element import FrameElement

# represents a layer on the frame itself
class FrameLayer(FrameElement):

    def __init__(self, layer, **kwargs):
        super().__init__(**kwargs)
        self.layer = layer

    def _render(self, img, card):
        img.paste(self.layer, (0,0))