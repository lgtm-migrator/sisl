from .basic import RangeInput


class ErangeInput(RangeInput):

    def __init__(self, key, name="Energy range", default=None,
        params={"step": 1}, help="The energy range that is displayed", **kwargs):

        super().__init__(key=key, name=name, default=default,
                         params=params, help=help, **kwargs)
