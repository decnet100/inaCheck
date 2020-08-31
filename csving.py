import csv


def init(file, header=''):
    with open(file, 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(header)


def write(file, data):
    with open(file, 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(data)


def read(file, header=None):
    output = []
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            output.append(row)
    return output
