class DicToObj:

    def __init__(self, prams):
        for key, value in prams.items():
            setattr(self, key, value)