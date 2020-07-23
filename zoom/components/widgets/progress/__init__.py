

from zoom.component import DynamicComponent

class ProgressWidget(DynamicComponent):
    """ProgressWidget

    >>> progress = ProgressWidget()
    >>> component = progress.format(
    ...    title='Widget Title',
    ...    hint='Widget hint',
    ...    value=75,
    ... )

    """

