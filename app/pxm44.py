"""PrimeXM FIX message definitions"""

import quickfix as fix


class MassQuote(fix.Message):
    """PrimeXM flavour of a MassQuote"""
    def __init__(self, *args):
        super().__init__(*args)
        self.getHeader().setField(fix.MsgType('i'))

    class NoQuoteSets(fix.Group):  # 296
        def __init__(self):
            order = fix.IntArray(3)
            order[0] = 302      # QuoteSetID
            order[1] = 295      # NoQuoteEntries
            order[2] = 0
            super().__init__(296, order[0], order)

        class NoQuoteEntries(fix.Group):  # 295
            def __init__(self):
                order = fix.IntArray(7)
                order[0] = 299  # QuoteEntryID
                order[1] = 106  # Issuer
                order[2] = 134  # BidSize
                order[3] = 135  # OfferSize
                order[4] = 188  # BidSpotRate
                order[5] = 190  # OfferSpotRate
                order[6] = 0
                super().__init__(295, order[0], order)


class MarketDataSnapshotFullRefresh(fix.Message):
    """PrimeXM flavour of a MarketDataSnapshotFullRefresh"""
    def __init__(self, *args):
        super().__init__(*args)
        self.getHeader().setField(fix.MsgType('W'))

    class NoMDEntries(fix.Group):  # 268
        def __init__(self):
            order = fix.IntArray(6)
            order[0] = 269  # MDEntryType
            order[1] = 270  # MDEntryPx
            order[2] = 271  # MDEntrySize
            order[3] = 299  # QuoteEntryID
            order[4] = 106  # Issuer
            order[5] = 0
            super().__init__(268, order[0], order)
