def is_valid_parentheses(parens):
    stack = []
    opening_parens = {'(', '[', '{'}
    closing_parens = {')', ']', '}'}

    for char in parens:
        if char in opening_parens:
            stack.append(char)
        elif char in closing_parens:
            if not stack:
                return False

            top = stack.pop()
            if (char == ')' and top != '(') or (char == ']' and top != '[') or (char == '}' and top != '{'):
                return False

    return len(stack) == 0
