def yes_no(prompt):
    """
    Prompt the user with a yes/no question until an answer is received

    :param prompt: the message to display
    :type prompt: str
    :return: whether the user answered yes or no
    :rtype: bool
    """
    while True:
        resp = input('{0} (Y/N) '.format(prompt.strip())).lower().strip()

        if resp == 'y' or resp == 'yes':
            return True
        elif resp == 'n' or resp == 'no':
            return False


def convert_xml_to_dict(root_node):
    """
    Convert an XML ElementTree to a dictionary

    This is only designed to support Gelbooru's idiosyncratic XML layout where all information
    is stored in attributes. It is not meant to handle all cases.

    :param root_node: the XML tree of post metadata
    :type root_node: xml.etree.ElementTree.Element
    :return: a dictionary equivalent of the XML
    :rtype: dict
    """
    new_dict = {}

    for key, value in root_node.items():
        try:
            new_dict[key] = int(value)
        except ValueError:
            new_dict[key] = value

    children = root_node.getchildren()

    if children:
        new_dict[root_node.tag] = [convert_xml_to_dict(child) for child in children]

    return new_dict
