import requests
import sys

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar

    Parameters:
        iteration (int) : current iteration
        total (int) : total iterations
        prefix (str): prefix string (default '')
        suffix (str) : suffix string (default '')
        decimals (int) : positive number of decimals in percent complete (default 1)
        bar_length (int) : character length of bar (default 100)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def signal_handler(sig, frame):
    sys.stdout.flush()
    print('You pressed Ctrl+C!')
    sys.exit(0)

def flatten(items, seqtypes=(list, tuple)):
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    return items

def tabulate(data, header, max_width=80, align='left'):
    """
    Tabulate list of lists with header

    Params:
        data (list of lists): data to fill the table
        header (list): header of the table
        max_width (int): maximum length of the table (currently unimplemented, default 80)
        align (str): alignment of fields in the table (currently unimplemented, default left)

    """
    if not all(map(lambda x: len(x) == len(header), data)):
        print("sorry, but the table is misbuild!")

    #removing trailing space and stringify data

    data = [[str(elem).strip() for elem in lst] for lst in data]
    columns_width = [max([len(elem) for elem in sublst] + [len(header[i])]) for i, sublst in enumerate(zip(*data))]
    print('| ' + ' + '.join(["-" * w for w in columns_width]) + ' |')
    print('| ' + ' | '.join([h + ' ' * (columns_width[i] - len(h)) for i,h in enumerate(header)]) + ' |')
    print('| ' + ' + '.join(["-"*w for w in columns_width]) + ' |')
    for line in data:
        print('| ' + ' | '.join([d + ' ' * (columns_width[i] - len(d)) for i,d in enumerate(line)]) + ' |')
    print('| ' + ' + '.join(["-"*w for w in columns_width]) + ' |')

def check_connection():
    """
    Check if there is internet connection.

    Returns:
        bool: true if there is internet connection, false otherwise
    """
    try:
        requests.head("http://google.com", allow_redirects=True)
        return True
    except :
        return False


