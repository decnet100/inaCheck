import subprocess


def get_tag_from_file(file, tag):
    return subprocess.check_output('exiftool -%s -s -s -s "%s"' % (tag, file))[:-2]  # remove last /r/n
