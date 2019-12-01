
def columnize(data, divider="|", headers=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = "{}".format(divider)
    for i, row in enumerate(rows):
        if headers is not None and headers == i:
            r += divider.join(map(lambda x: "-" * (x), widths )) + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

    
