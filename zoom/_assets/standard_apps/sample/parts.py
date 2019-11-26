"""
    sample parts
"""

from zoom.component import Component
from zoom.page import page
from zoom.response import CSSResponse, JavascriptResponse
from zoom.tools import markdown
from zoom.mvc import View

class MyView(View):

    def index(self):
        content = Component(markdown("""
        Parts
        ====
        * <div class="component-pink">component styles makes this pink</div>
        * <div class="component-green">component css makes this green</div>
        * <div class="component-chocolate">component libs makes this chocolate</div>
        * <div class="component-magenta">component js makes this magenta</div>
        * <div class="component-coral">component head makes this coral</div>
        * <div class="component-tomato">component tail makes this tomato</div>
        * <div class="page-slategray">page styles makes this slategray</div>
        * <div class="page-red">page css makes this red</div>
        * <div class="page-purple">page libs makes this purple</div>
        * <div class="page-cyan">page js makes this cyan</div>
        * <div class="page-navy">page head makes this navy</div>
        * <div class="page-olive">page tail makes this olive</div>
        """),
            styles=['/sample/parts/mystyle'],
            css=".component-green {color: green}",
            libs=['/sample/parts/mylib'],
            js='$(".component-magenta").css("color", "magenta")',
            head='<style>.component-coral {color: coral}</style>',
            tail='<script>$(".component-tomato").css("color", "tomato")</script>',
        )
        return page(
            content,
            styles=['/sample/parts/pagestyle'],
            css='.page-red {color: red}',
            libs=['/sample/parts/pagelib'],
            js='$(".page-cyan").css("color", "cyan")',
            head='<style>.page-navy {color: navy}</style>',
            tail='<script>$(".page-olive").css("color", "olive")</script>',
        )

    def mystyle(self):
        return CSSResponse('.component-pink {color: pink}'.encode('utf8'))

    def pagestyle(self):
        return CSSResponse('.page-slategray {color: slategray}'.encode('utf8'))

    def mylib(self):
        return JavascriptResponse(
            '$(".component-chocolate").css("color", "chocolate")'.encode('utf8')
        )

    def pagelib(self):
        return JavascriptResponse(
            '$(".page-purple").css("color", "purple")'.encode('utf8')
        )


view = MyView()
