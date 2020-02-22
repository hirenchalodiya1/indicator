import backtrader as bt


class StochasticStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self, only_positions=False):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.cheating = self.cerebro.p.cheat_on_open

        # Add a MovingAverageSimple indicator
        self.st = bt.ind.StochasticFast(period=3)
        self.only_positions = only_positions

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

    def operate(self):
        self.log(f'Close, {self.dataclose[0]}')
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if self.only_positions:
            if self.buy_approved():
                self.order = self.buy()
            if self.sell_approved():
                self.sell_approved()
            return

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.buy_approved():
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.sell_approved():
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Next:: Close, %.2f' % self.dataclose[0])
        # print(self.st.lines.percK[0], self.st.lines.percD[0], self.st.lines.percK[-1])

        if self.cheating:
            return
        self.operate()

    def next_open(self):
        # self.log('NextOpen:: Close, %.2f' % self.dataclose[0])
        if not self.cheating:
            return
        self.operate()

    def buy_approved(self):
        return self.st.lines.percK[0] <= self.st.lines.percD[0] \
               and self.st.lines.percK[1] >= self.st.lines.percD[1] \
               and self.st.lines.percK[0] <= self.st.params.lowerband

    def sell_approved(self):
        return self.st.lines.percK[0] >= self.st.lines.percD[0] \
               and self.st.lines.percK[1] <= self.st.lines.percD[1] \
               and self.st.lines.percK[0] >= self.st.params.upperband

    def getsizing(self, data=None, isbuy=None):
        if isbuy:
            self.stakes = int(self.cerebro.broker.getcash() // self.data_open[0])
        return self.stakes
