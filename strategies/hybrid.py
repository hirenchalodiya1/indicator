import backtrader as bt
from indicators import DonchianChannels


class DonchialtorXStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        """
        Logging function fot this strategy
        """

        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self, only_positions=False):
        # Keep a reference to the "close" line in the data[0] data series
        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.cheating = self.cerebro.p.cheat_on_open

        # Add a MovingAverageSimple indicator
        self.don = DonchianChannels(period=20)
        self.st = bt.ind.StochasticFast(period=14, upperband=75, lowerband=25)
        self.ad = bt.ind.AverageDirectionalMovementIndexRating(period=14)
        self.crossover = bt.ind.CrossOver(self.don.lines.dcm, self.dataclose)

        self.stakes = 10
        self.state = 'BUY'
        self.only_positions = only_positions

        self.cerebro.positive = 0
        self.cerebro.negative = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

        if trade.pnl >= 0:
            self.cerebro.positive += 1
        else:
            self.cerebro.negative += 1

    def next(self):
        # Simply log the closing price of the series from the reference
        if self.cheating:
            return
        self.operate()

    def next_open(self):
        if not self.cheating:
            return
        self.operate()

    def operate(self):
        self.log(f'Close, {self.dataclose[0]}')
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # do pre processing
        self.pre_operate()

        if self.only_positions:
            if self.buy_approved():
                self.buy()
            if self.sell_approved():
                self.sell()
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.buy_approved():
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.data_open[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.sell_approved():
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def pre_operate(self):
        self.donchian()

    def buy_approved(self):
        return self.state is 'BUY' \
               and 'BUY' in self.oscillator() \
               and self.adx()

    def sell_approved(self):
        return self.state is 'SELL' \
               and 'SELL' in self.oscillator() \
               and self.adx()

    def donchian(self):
        if self.data_low[0] == self.don.lines.dcl[1]:
            self.state = 'BUY'
        if self.data_high[0] == self.don.lines.dch[1]:
            self.state = 'SELL'

    def oscillator(self):
        # %K crosses %D upwards
        if self.st.lines.percK[0] <= self.st.lines.percD[0] \
                and self.st.lines.percK[1] >= self.st.lines.percD[1]:

            if self.st.lines.percK[0] <= self.st.params.lowerband:
                return ['BUY']
            else:
                return ['MAYBE_BUY']

        # %K crosses %D downwards
        elif self.st.lines.percK[0] >= self.st.lines.percD[0] \
                and self.st.lines.percK[1] <= self.st.lines.percD[1]:

            if self.st.lines.percK[0] >= self.st.params.upperband:
                return ['SELL']
            else:
                return ['MAYBE_SELL']

        else:
            return ['NOTHING']

    def adx(self):
        # print('ADX: %s , %s' % (self.ad[1], self.ad[0]))
        if self.ad.lines.adx[1] >= 22:
            return True
        else:
            return False

    def getsizing(self, data=None, isbuy=None):
        if self.only_positions:
            return 1
        if isbuy:
            self.stakes = int(self.cerebro.broker.getcash() // self.data_open[0])
        return self.stakes
