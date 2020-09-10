

from zoom.component import DynamicComponent

class ProgressWidget(DynamicComponent):
    """ProgressWidget

    >>> progress = ProgressWidget()
    >>> component = progress.format(
    ...    title='Widget Title',
    ...    hint='Widget hint',
    ...    percent=75,
    ... )

    """

    def format(
            self,
            percent,
            title='value title',
            hint='',
            color='#337ab7',
        ):
        return DynamicComponent.format(
            self,
            percent=percent,
            title=title,
            hint=hint,
            color=color,
        )
