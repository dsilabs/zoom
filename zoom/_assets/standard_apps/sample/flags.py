"""Flag samples."""

import zoom

from zoom.mvc import View
from zoom.components import TextFlag

class FlagSampleView(View):

    def index(self):
        custom_text_flag = TextFlag(on_label="Turn me off", off_label="Turn me on")

        return zoom.page('''<div id="flag-samples">
            <style>
                #flag-samples strong {
                    display: inline-block;
                    width: 200px;
                }
            </style>
            <h1>Flags</h1>
            <p>
                Flags are per-user togglable elements that remember
                their state.
            </p>
            <strong>Text flag:</strong> {{text_flag}}<br/>
            <strong>Icon flag:</strong> {{icon_flag}}<br/>
            <strong>Checkbox flag:</strong> {{checkbox_flag}}<br/>
            <strong>Customized text flag:</strong> %s<br/>
            <strong>Customized icon flag:</strong> {{icon_flag icon="thumbs-up" on_color="red" off_color="blue"}}
        </div>'''%(str(custom_text_flag)))

view = FlagSampleView()
