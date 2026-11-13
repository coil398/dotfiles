FIELDS = {'product': {'sku': {'type': 'str', 'required': True},
             'title': {'type': 'str', 'required': True},
             'price_cents': {'type': 'int', 'required': True, 'min': 0},
             'stock': {'type': 'int', 'required': False, 'min': 0}}}
