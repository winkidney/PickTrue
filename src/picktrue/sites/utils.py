import hashlib


def _get_file_hash(file_content):
    m = hashlib.md5()
    m.update(file_content)
    return m.digest().hex()


def _get_name_ext_from_url(img_url):
    file_name = img_url.split(
        '/'
    )[-1]
    if "?" in file_name:
        file_name = file_name.split('?')[:-1]
        file_name = '?'.join(file_name)
    name = file_name.split('.')[:-1]
    name = ".".join(name)
    ext = file_name.split('.')[-1]
    return name, ext


def get_filename_fom_url(img_url):
    name, ext = _get_name_ext_from_url(img_url)
    return ".".join((name, ext))


def get_name_with_hash_from_url(img_url: str, file_content):
    name, ext = _get_name_ext_from_url(img_url)
    name_postfix = _get_file_hash(file_content)
    file_name = "-".join([name, name_postfix])
    file_name = ".".join([file_name, ext])
    return file_name


def safe_file_name(file_name):
    file_name = file_name.replace("/", "_")
    file_name = file_name.replace("?", "__")
    file_name = file_name.replace(":", "___")
    return file_name