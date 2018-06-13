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
