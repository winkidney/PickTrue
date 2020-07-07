from picktrue.sites import utils


def test_get_name_ext_from_url():
    assert utils.get_filename_fom_url(
        "https://img9.doubanio.com/view/photo/l/public/p2208623414.jpg"
    ) == "p2208623414.jpg"

    assert utils.get_filename_fom_url(
        "https://img9.doubanio.com/view/photo/l/public/p2208623414.jpg?hello=world"
    ) == "p2208623414.jpg"
