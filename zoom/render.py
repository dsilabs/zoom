"""
    zoom.render

    rendering tools
"""

from zoom.fill import dzfill


def apply_helpers(template, obj, providers):
    def not_found(name):
        """what happens when a helper is not found"""
        def missing_helper(*args, **kwargs):
            """provide some info for missing helpers"""
            parts = ' '.join(
                [name] +
                ['{!r}'.format(a) for a in args] +
                ['{}={!r}'.format(k, v) for k, v in kwargs.items()]
            )
            return '&lt;dz:{}&gt; missing'.format(
                parts,
            )
        return missing_helper

    def filler(helpers):
        """callback for filling in templates"""
        def _filler(name, *args, **kwargs):
            """handle the details of filling in templates"""

            if hasattr(obj, name):
                attr = getattr(obj, name)
                if callable(attr):
                    repl = attr(obj, *args, **kwargs)
                else:
                    repl = attr
                return dzfill(repl, _filler)

            helper = helpers.get(name, not_found(name))
            if callable(helper):
                repl = helper(*args, **kwargs)
            else:
                repl = helper
            return dzfill(repl, _filler)
        return _filler
    helpers = {}
    for provider in providers:
        helpers.update(provider)
    return dzfill(template, filler(helpers))