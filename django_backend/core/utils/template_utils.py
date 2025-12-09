'''
Description: Template Manager
            - load template file with parameters
'''


import logging

from django.template import loader

from core.core.exception import IkException

logger = logging.getLogger('ikyo')


def loadTemplateFile(templateFile, parameters=None) -> str:
    """This is load html file content with parameters method.

    Args:
        templateFile (str): The template file relative path. 
                            eg: './ikyo/EL/EL002/note1.html'
        parameters (dict, optional):  The data for load template file content.

    Returns:
        str: If have parameters, It's template file content after auto load parameters.
             IF haven't parameters, Just template file content

    Raises:
        IkException: backend.core.exception.IkException

    """
    if templateFile is None:
        raise IkException('Parameter [templateFile] is mandatory.')
    t = loader.get_template(templateFile)
    content = t.render({} if parameters is None else parameters)
    return content
