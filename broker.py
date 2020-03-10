from __future__ import (absolute_import, division, print_function, unicode_literals)
from datetime import datetime
import backtrader as bt
from feeds import YahooFinanceData
from strategies import DonchialtorXStrategy as Str
import sys


def main(strategy, stock_name='RS', only_positions=False):
    # Add new cerebro engine
    with open('terminal.log', 'a') as f:
        # sys.stdout = f

        print(stock_name + " starts")

        cerebro = bt.Cerebro(cheat_on_open=True, stdstats=False)
        cerebro.addobserver(bt.observers.BuySell)
        if not only_positions:
            cerebro.addobserver(bt.observers.Trades)

        # set cash
        cerebro.broker.setcash(5000)

        # Add new strategy to cerebro
        if only_positions:
            cerebro.addstrategy(strategy, only_positions=only_positions)
        else:
            cerebro.addstrategy(strategy)

        # feed data to cerebro engine
        data0 = YahooFinanceData(dataname=stock_name,
                                 fromdate=datetime(2019, 2, 1),
                                 todate=datetime(2020, 2, 1),
                                 adjclose=False)
        # print(dir(data0))
        cerebro.adddata(data0)

        ini = cerebro.broker.getvalue()
        print('Starting Portfolio Value: %.2f' % ini)

        # run cerebro
        cerebro.run()

        final = cerebro.broker.getvalue()
        print('Final Portfolio Value: %.2f' % final)

        # profit
        print('Profit: %.2f, Profit : %.2f%s' % (final - ini, (final * 100 / ini - 100), chr(37) ))

        # print accuracy
        if hasattr(cerebro, 'positive') and hasattr(cerebro, 'negative'):
            try:
                print('Trading Accuracy : %.2f%s' %((cerebro.positive*100/(cerebro.positive+cerebro.negative)) , chr(37)))
            except:
                pass
        
        if hasattr(cerebro, 'wrong_count') and hasattr(cerebro, 'total_count'):
            wrong_predictions = cerebro.wrong_count
            total_predictions = cerebro.total_count
            print('Prediction Accuracy : %.2f%s' %(((total_predictions - wrong_predictions)*100/total_predictions) , chr(37))) 
        # plot in cerebro
        cerebro.plot()



if __name__ == "__main__":
    main(Str, 'GOOGL')
