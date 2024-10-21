import os
from datetime import datetime

from mov_to_mp4 import get_file_creation_date, get_output_filepath


def test_get_file_creation_date(tmp_path):

    test_file = tmp_path / "test_file.txt"
    test_file.touch()

    creation_time = os.path.getctime(test_file)
    expected_date = datetime.fromtimestamp(creation_time).strftime("%Y%m%d")

    result = get_file_creation_date(str(test_file))

    assert result == expected_date


def test_get_output_filepath(tmp_path):
    test_file = tmp_path / "test_file.mov"
    test_file.touch()

    file_creation_date = get_file_creation_date(test_file)
    result = get_output_filepath(test_file)

    expected_path = tmp_path / f"{file_creation_date}_test_file.mp4"
    assert result == str(expected_path)
