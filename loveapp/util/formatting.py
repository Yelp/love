def format_loves(loves):
    # organise loves into two roughly equal lists for displaying
    if len(loves) < 20:
        loves_list_one = loves
        loves_list_two = []
    else:
        loves_list_one = loves[:len(loves)//2]
        loves_list_two = loves[len(loves)//2:]

        if len(loves_list_one) < len(loves_list_two):
            loves_list_one.append(loves_list_two.pop())
    return loves_list_one, loves_list_two
