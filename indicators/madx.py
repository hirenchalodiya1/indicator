import backtrader as bt


class MADX(bt.ind.AverageDirectionalMovementIndex):
    '''
    Defined by Hiren, Sr. in 2020.
    '''
    alias = ('MDXR',)
    params = (
        ('mperiod', 5),
        ('movav', bt.ind.MovAv.Simple)
    )
    lines = ('mdxr',)
    plotlines = dict(adxr=dict(_name='MDXR'))

    def __init__(self):
        super(MADX, self).__init__()
        self.lines.mdxr = self.p.movav(self.l.adx, period=self.p.mperiod)
