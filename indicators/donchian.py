import backtrader as bt


class DonchianChannels(bt.Indicator):
    '''
    Params Note:
      - `lookback` (default: -1)
        If `-1`, the bars to consider will start 1 bar in the past and the
        If `0`, the current prices will be considered for the Donchian
        Channel. This means that the price will **NEVER** break through the
        upper/lower channel bands.
    '''

    alias = ('DCH', 'DonchianChannel',)

    lines = ('dcm', 'dch', 'dcl')  # dc middle, dc high, dc low
    params = dict(
        period=10,
        lookback=0,  # consider current bar or not
    )

    plotinfo = dict(subplot=False, plotlinelabels=True)  # plot along with data
    plotlines = dict(
        dcm=dict(ls='--', _name='M'),  # dashed line
        dch=dict(
            _samecolor=False,
             _name='HH',
              color='blue',
               _fill_gt=('dcm', 'orange')
               ),
        dcl=dict(
            _samecolor=True,
             _name='LL',
              color='blue',
               _fill_lt=('dcm', 'green')
               ),
        high=dict(_samecolor=False, _name='H', color='orange'),
        low=dict(_samecolor=False, _name='L', color='green')
    )

    def __init__(self):
        hi, lo = self.data.high, self.data.low
        if self.p.lookback:  # move backwards as needed
            hi, lo = hi(self.p.lookback), lo(self.p.lookback)

        self.l.dch = bt.ind.Highest(hi, period=self.p.period)
        self.l.dcl = bt.ind.Lowest(lo, period=self.p.period)
        self.l.dcm = (self.l.dch + self.l.dcl) / 2.0  # avg of the above
        self.l.high = hi
        self.l.low = lo
