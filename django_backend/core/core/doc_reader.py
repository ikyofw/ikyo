from pathlib import Path
import core.core.fs as ikfs

NOT_EXISTS_FILE_TEMPLATE = 'notExists.pdf'
BLANK_PAGE_FILE_TEMPLATE = 'blankPage.pdf'


def get_not_exist_file_template() -> Path:
    return ikfs.getLastRevisionFile("core/resources/templates/file", NOT_EXISTS_FILE_TEMPLATE)


def get_blank_page_file_template() -> Path:
    return ikfs.getLastRevisionFile("core/resources/templates/file", BLANK_PAGE_FILE_TEMPLATE)
