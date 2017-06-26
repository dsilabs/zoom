
This theme is built using pug and sass.  A great way to modify
this sort of theme is to use both pug and sass in watch mode
allowing you to make changes to the source files and with the
resulting .html and .css files being regenerated as you save
changes.

To do this, you'll need both pug and sass installed as well as
pug-cli.  Then, in two separate windows, swith to the theme
directory (zoom/web/themes/default in this case) and run the
commands in each window:

window 1:
  pug -w --pretty src/pug/pages --out .

window 2:
  sass  --style compressed --sourcemap=none --watch src/sass:css

Adust parameters as you see fit.
